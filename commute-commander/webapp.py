"""Commute Commander web server.

Run with:  python webapp.py
Visit:     http://localhost:8000

Endpoints
---------
GET  /api/history                              list past sessions (newest 20)
GET  /api/history/{session_id}                 full session detail
GET  /api/briefing/{session_id}/{section}      poll one section
POST /api/briefing                             run full briefing, returns structured JSON
POST /api/briefing/{session_id}/{section}/refresh   re-run one agent
POST /api/briefing/{session_id}/save           pin/save a briefing to disk
POST /api/briefing/{session_id}/rerun          re-run all agents with current intent
PATCH /api/briefing/{session_id}/intent        update intent fields, optionally re-run
"""

from __future__ import annotations

import json
import re
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from agents.orchestrator import OrchestratorAgent
from services.session_manager import SessionManager


ROOT             = Path(__file__).resolve().parent
STATIC_DIRECTORY = ROOT / "web"
session_manager  = SessionManager()
orchestrator     = OrchestratorAgent(session_manager=session_manager)

# ── URL patterns ────────────────────────────────────────────
_SECTION_RE = r"(?P<section>weather|news|commute|breakfast)"
_SID_RE     = r"(?P<session_id>[^/]+)"

_RE_BRIEFING        = re.compile(r"^/api/briefing$")
_RE_SECTION_POLL    = re.compile(rf"^/api/briefing/{_SID_RE}/{_SECTION_RE}$")
_RE_SECTION_REFRESH = re.compile(rf"^/api/briefing/{_SID_RE}/{_SECTION_RE}/refresh$")
_RE_SAVE            = re.compile(rf"^/api/briefing/{_SID_RE}/save$")
_RE_RERUN           = re.compile(rf"^/api/briefing/{_SID_RE}/rerun$")
_RE_INTENT          = re.compile(rf"^/api/briefing/{_SID_RE}/intent$")
_RE_HISTORY_DETAIL  = re.compile(rf"^/api/history/{_SID_RE}$")


def _get_intent(session_id: str) -> dict:
    """Return intent from disk (survives restarts). Falls back to empty dict."""
    return session_manager.get_intent(session_id) or {}


class CommuteCommanderHandler(SimpleHTTPRequestHandler):
    """Serves static UI files and the structured JSON API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIRECTORY), **kwargs)

    # ── GET ─────────────────────────────────────────────────
    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        if path == "/api/history":
            self._handle_history_list()
            return

        m = _RE_HISTORY_DETAIL.match(path)
        if m:
            self._handle_history_detail(m.group("session_id"))
            return

        m = _RE_SECTION_POLL.match(path)
        if m:
            self._handle_section_poll(m.group("session_id"), m.group("section"))
            return

        super().do_GET()

    # ── POST ─────────────────────────────────────────────────
    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        if _RE_BRIEFING.match(path):
            self._handle_briefing()
            return

        m = _RE_SECTION_REFRESH.match(path)
        if m:
            self._handle_section_refresh(m.group("session_id"), m.group("section"))
            return

        m = _RE_SAVE.match(path)
        if m:
            self._handle_save(m.group("session_id"))
            return

        m = _RE_RERUN.match(path)
        if m:
            self._handle_rerun(m.group("session_id"))
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    # ── PATCH ────────────────────────────────────────────────
    def do_PATCH(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        m = _RE_INTENT.match(path)
        if m:
            self._handle_patch_intent(m.group("session_id"))
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    # ── Route handlers ───────────────────────────────────────

    def _handle_briefing(self) -> None:
        """POST /api/briefing — main entry point."""
        try:
            body   = self._read_json_body()
            query  = str(body.get("query", "")).strip()
            user_id = str(body.get("user_id", "guest")).strip() or "guest"

            if not query:
                raise ValueError("Please enter what you would like in your briefing.")

            session_id = session_manager.start_session(user_id)

            # Run structured with a 30-second hard timeout so the browser
            # never hangs silently if an upstream API is slow.
            result_box: dict = {}
            error_box:  list = []

            def _run() -> None:
                try:
                    result_box["data"] = orchestrator.run_structured(
                        query, session_id=session_id
                    )
                except Exception as exc:
                    error_box.append(exc)

            t = threading.Thread(target=_run, daemon=True)
            t.start()
            t.join(timeout=30)

            if error_box:
                raise error_box[0]
            if "data" not in result_box:
                raise TimeoutError(
                    "The briefing took too long. Check your network connection and try again."
                )

            structured = result_box["data"]

            # Persist intent to disk so it survives restarts
            intent = structured.get("intent", {})
            session_manager.save_intent(session_id, intent)

            self._send_json(HTTPStatus.OK, {
                "session_id": session_id,
                "intent":     intent,
                "sections":   structured.get("sections", {}),
                "briefing":   "\n\n".join(
                    str(s.get("data", ""))
                    for s in structured.get("sections", {}).values()
                    if s.get("status") == "success"
                ),
            })

        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception as exc:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": f"Could not create the briefing: {exc}"},
            )

    def _handle_section_refresh(self, session_id: str, section: str) -> None:
        """POST /api/briefing/{id}/{section}/refresh"""
        intent = _get_intent(session_id)
        result = orchestrator.run_section(section, intent)
        self._send_json(HTTPStatus.OK, result)

    def _handle_section_poll(self, session_id: str, section: str) -> None:
        """GET /api/briefing/{id}/{section}"""
        intent = _get_intent(session_id)
        if not intent:
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {
                    "section": section,
                    "status":  "error",
                    "error":   {"code": "session_not_found", "message": "Session not found."},
                },
            )
            return
        result = orchestrator.run_section(section, intent)
        self._send_json(HTTPStatus.OK, result)

    def _handle_save(self, session_id: str) -> None:
        """POST /api/briefing/{id}/save — pin the current briefing."""
        # Re-run all sections with the stored intent so we have fresh data to persist
        intent = _get_intent(session_id)
        if not intent:
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"saved": False, "error": {"code": "session_not_found", "message": "Session not found."}},
            )
            return

        sections: dict = {}
        for sec in intent.get("sections", []):
            sections[sec] = orchestrator.run_section(sec, intent)

        ok = session_manager.save_briefing(session_id, sections)
        if ok:
            self._send_json(HTTPStatus.OK, {"saved": True, "session_id": session_id})
        else:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"saved": False, "error": {"code": "write_failed", "message": "Briefing not saved — retry?"}},
            )

    def _handle_rerun(self, session_id: str) -> None:
        """POST /api/briefing/{id}/rerun — re-run all agents with the stored intent."""
        intent = _get_intent(session_id)
        if not intent:
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"error": {"code": "session_not_found", "message": "Session not found."}},
            )
            return

        results: dict = {}
        for sec in intent.get("sections", []):
            results[sec] = orchestrator.run_section(sec, intent)

        session_manager.log_interaction(session_id, {"event": "rerun", "sections": list(results.keys())})
        self._send_json(HTTPStatus.OK, {"session_id": session_id, "intent": intent, "sections": results})

    def _handle_patch_intent(self, session_id: str) -> None:
        """PATCH /api/briefing/{id}/intent — update intent fields and persist."""
        try:
            body   = self._read_json_body()
            intent = _get_intent(session_id)
            if not intent:
                intent = {}

            # Merge only recognised fields
            for field in ("location", "sections", "ingredients", "time_constraint", "travel_intent"):
                if field in body:
                    intent[field] = body[field]

            session_manager.save_intent(session_id, intent)
            self._send_json(HTTPStatus.OK, {"session_id": session_id, "intent": intent})

        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def _handle_history_list(self) -> None:
        """GET /api/history"""
        try:
            sessions = session_manager.list_sessions(limit=20)
            self._send_json(HTTPStatus.OK, {"sessions": sessions})
        except Exception as exc:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": f"Could not load history: {exc}"},
            )

    def _handle_history_detail(self, session_id: str) -> None:
        """GET /api/history/{session_id}"""
        data = session_manager.get_session(session_id)
        if data is None:
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"error": {"code": "not_found", "message": f"Session {session_id!r} not found."}},
            )
            return
        self._send_json(HTTPStatus.OK, data)

    # ── Helpers ──────────────────────────────────────────────

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        encoded = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type",   "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt: str, *args) -> None:  # suppress per-request noise
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), CommuteCommanderHandler)
    print("Commute Commander → http://localhost:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
