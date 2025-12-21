# api/session_store.py
from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Dict, Optional
from uuid import uuid4
import os
import time


@dataclass(frozen=True)
class SessionInfo:
    session_id: str
    db_path: str
    created_at: float


class SessionStore:
    """
    session_id -> db_path (solo rutas, NUNCA conexiones)
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._sessions: Dict[str, SessionInfo] = {}

    def open_existing(self, db_path: str) -> SessionInfo:
        db_path = os.path.abspath(db_path)
        if not os.path.exists(db_path):
            raise FileNotFoundError(db_path)

        sid = uuid4().hex
        info = SessionInfo(session_id=sid, db_path=db_path, created_at=time.time())
        with self._lock:
            self._sessions[sid] = info
        return info

    def register(self, db_path: str) -> SessionInfo:
        db_path = os.path.abspath(db_path)
        sid = uuid4().hex
        info = SessionInfo(session_id=sid, db_path=db_path, created_at=time.time())
        with self._lock:
            self._sessions[sid] = info
        return info

    def get(self, session_id: str) -> Optional[SessionInfo]:
        with self._lock:
            return self._sessions.get(session_id)

    def close(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None
