import json
import os
from datetime import datetime
from typing import Any, Dict, List


class SessionManager:
    def __init__(self, storage_dir: str | None = None) -> None:
        self.storage_dir = storage_dir or os.path.join(os.getcwd(), "sessions")
        os.makedirs(self.storage_dir, exist_ok=True)

    def start_session(self, user_id: str) -> str:
        session_id = f"{user_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "interactions": [],
        }
        self._write(session_id, payload)
        return session_id

    def log_interaction(self, session_id: str, interaction: Dict[str, Any]) -> None:
        payload = self._read(session_id)
        payload.setdefault("interactions", []).append(
            {
                **interaction,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        self._write(session_id, payload)

    def _write(self, session_id: str, payload: Dict[str, Any]) -> None:
        path = os.path.join(self.storage_dir, f"{session_id}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def _read(self, session_id: str) -> Dict[str, Any]:
        path = os.path.join(self.storage_dir, f"{session_id}.json")
        if not os.path.exists(path):
            return {"session_id": session_id, "interactions": []}
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
