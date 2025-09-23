"""
Agent Session Manager for multi-user support.

This module provides session management for theological agents, allowing
multiple users to maintain separate conversation contexts.
"""

import logging
import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta, timezone
import threading

from .theological_agent import TheologicalAgent

logger = logging.getLogger(__name__)


class AgentSessionManager:
    """
    Manages sessions for theological agents, providing multi-user support
    with automatic cleanup and session isolation.
    """

    def __init__(self, session_timeout_minutes: int = 30):
        """
        Initialize the session manager.

        Args:
            session_timeout_minutes: Minutes after which inactive sessions expire
        """
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self._lock = threading.Lock()
        logger.info(f"Initialized AgentSessionManager with {session_timeout_minutes}min timeout")

    def get_or_create_session(self, session_id: Optional[str] = None) -> tuple[str, TheologicalAgent]:
        """
        Get an existing session or create a new one.

        Args:
            session_id: Optional existing session ID

        Returns:
            Tuple of (session_id, theological_agent)
        """
        with self._lock:
            # Clean up expired sessions first
            self._cleanup_expired_sessions()

            # If no session_id provided or session doesn't exist, create new one
            if not session_id or session_id not in self.sessions:
                session_id = str(uuid.uuid4())
                self.sessions[session_id] = {
                    'agent': TheologicalAgent(),
                    'created_at': datetime.now(timezone.utc),
                    'last_accessed': datetime.now(timezone.utc)
                }
                logger.info(f"Created new session: {session_id}")
            else:
                # Update last accessed time
                self.sessions[session_id]['last_accessed'] = datetime.now(timezone.utc)
                logger.debug(f"Retrieved existing session: {session_id}")

            return session_id, self.sessions[session_id]['agent']

    def get_session(self, session_id: str) -> Optional[TheologicalAgent]:
        """
        Get an existing session's agent.

        Args:
            session_id: Session ID to retrieve

        Returns:
            TheologicalAgent instance or None if session doesn't exist
        """
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id]['last_accessed'] = datetime.now(timezone.utc)
                return self.sessions[session_id]['agent']
            return None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a specific session.

        Args:
            session_id: Session ID to delete

        Returns:
            True if session was deleted, False if it didn't exist
        """
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Deleted session: {session_id}")
                return True
            return False

    def reset_session(self, session_id: str) -> bool:
        """
        Reset a session's conversation memory while keeping the session alive.

        Args:
            session_id: Session ID to reset

        Returns:
            True if session was reset, False if it didn't exist
        """
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id]['agent'].reset_conversation()
                self.sessions[session_id]['last_accessed'] = datetime.now(timezone.utc)
                logger.info(f"Reset conversation for session: {session_id}")
                return True
            return False

    def _cleanup_expired_sessions(self):
        """Remove sessions that have exceeded the timeout period."""
        current_time = datetime.now(timezone.utc)
        expired_sessions = []

        for session_id, session_data in self.sessions.items():
            if current_time - session_data['last_accessed'] > self.session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")

        if expired_sessions:
            logger.debug(f"Removed {len(expired_sessions)} expired sessions")

    def get_session_count(self) -> int:
        """Get the current number of active sessions."""
        with self._lock:
            self._cleanup_expired_sessions()
            return len(self.sessions)

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get information about a specific session.

        Args:
            session_id: Session ID to get info for

        Returns:
            Dictionary with session info or None if session doesn't exist
        """
        with self._lock:
            if session_id in self.sessions:
                session_data = self.sessions[session_id]
                return {
                    'session_id': session_id,
                    'created_at': session_data['created_at'].isoformat(),
                    'last_accessed': session_data['last_accessed'].isoformat(),
                    'age_minutes': (datetime.now(timezone.utc) - session_data['created_at']).total_seconds() / 60
                }
            return None