"""Commute Commander web server.

Run with:  python webapp.py
Visit:     http://localhost:8000
"""

from __future__ import annotations

import json
import re
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from agents.orchestrator import OrchestratorAgent
from services.session_manager import SessionManager


ROOT = Path(__file__).resolve().parent
STATIC_DIRECTORY = ROOT / "web"
session_manager = SessionManager()
orchestrator = OrchestratorAgent(session_manager=session_manager)

# In-memory store of the last intent per session, used by /refresh
_session_intents: dict[str, dict] = {}

# Route patterns
_RE_REFRESH = re.compile(
    r"^/api/briefing/(?P<session_id>[^/]+)/(?P<section>weather|news|commute|breakfast)/refresh$"
)
_RE_SECTION = re.compile(
    r"^/api/briefing/(?P<session_id>[^/]+)/(?P<section>weather|news|commute|breakfast)$"
)


class CommuteCommanderHandler(SimpleHTTPRequestHandler):
    """Serves the UI static files and the JSON API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIRECTORY), **kwargs)

    # ------------------------------------------------------------------ GET
    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        # GET /api/history
        if path == "/api/history":
            self._handle_history()
            return

        # GET /api/briefing/{session_id}/{section}  — poll a single section
        m = _RE_SECTION.match(path)
        if m:
            self._handle_get_section(m.group("session_id"), m.group("section"))
            return

        # Everything else — serve static files
        super().do_GET()

    # ----------------------------------------------------------------- POST
    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        # POST /api/briefing  — main query entry point
        if path == "/api/briefing":
            self._handle_briefing()
            return

        # POST /api/briefing/{session_id}/{section}/refresh
        m = _RE_REFRESH.match(path)
        if m:
            self._handle_refresh(m.group("session_id"), m.group("section"))
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    # -------------------------------------------------------- route handlers

    def _handle_briefing(self) -> None:
        try:
            body = self._read_json_body()
            query = str(body.get("query", "")).strip()
            user_id = str(body.get("user_id", "guest")).strip() or "guest"

            if not query:
                raise ValueError("Please enter what you would like in your briefing.")

            session_id = session_manager.start_session(user_id)

            # Always run structured; also keep legacy plain-text for fallback
            structured = orchestrator.run_structured(query, session_id=session_id)
            legacy_text = orchestrator.run(query, session_id=session_id)

            # Cache the intent for later /refresh calls
            _session_intents[session_id] = structured.get("intent", {})

            self._send_json(HTTPStatus.OK, {
                # Legacy field — keeps any old clients working
                "briefing": legacy_text,
                # New structured fields
                "session_id": session_id,
                "intent": structured.get("intent", {}),
                "sections": structured.get("sections", {}),
            })

        except (ValueError, json.JSONDecodeError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
        except Exception as error:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": f"Could not create the briefing: {error}"},
            )

    def _handle_refresh(self, session_id: str, section: str) -> None:
        intent = _session_intents.get(session_id, {})
        result = orchestrator.run_section(section, intent)
        self._send_json(HTTPStatus.OK, result)

    def _handle_get_section(self, session_id: str, section: str) -> None:
        """Poll endpoint — re-runs the section with the cached intent."""
        intent = _session_intents.get(session_id, {})
        if not intent:
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {
                    "section": section,
                    "status": "error",
                    "error": {"code": "session_not_found", "message": "Session not found."},
                },
            )
            return
        result = orchestrator.run_section(section, intent)
        self._send_json(HTTPStatus.OK, result)

    def _handle_history(self) -> None:
        try:
            sessions_dir = ROOT / "sessions"
            sessions = []
            if sessions_dir.exists():
                for f in sorted(sessions_dir.glob("*.json"), reverse=True)[:20]:
                    try:
                        data = json.loads(f.read_text(encoding="utf-8"))
                        # SessionManager stores a list of interactions
                        first = data[0] if isinstance(data, list) and data else {}
                        sessions.append(
                            {
                                "session_id": f.stem,
                                "created_at": first.get("timestamp", ""),
                                "query": first.get("query", ""),
                            }
                        )
                    except Exception:
                        pass
            self._send_json(HTTPStatus.OK, {"sessions": sessions})
        except Exception as error:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": f"Could not load history: {error}"},
            )

    # ------------------------------------------------------------ helpers

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        encoded = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt: str, *args) -> None:  # quieter logs
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
