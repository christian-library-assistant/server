"""
Agent RAG Service for handling agentic retrieval-augmented generation queries.

This service extracts the business logic from the /query-agent endpoints and provides
session management with theological agents.
"""

import logging
from typing import Dict, Any, Optional

from ...models.schemas import UserQuery, AssistantResponse
from ..agents.session_manager import AgentSessionManager
from ..callbacks.token_usage_callback import TokenUsageCallbackHandler
from .source_formatter import SourceFormatter
from .token_usage_tracker import get_token_tracker

logger = logging.getLogger(__name__)


class AgentRAGService:
    """
    Service for handling agent-based RAG queries with session management.
    """

    def __init__(self, session_manager: AgentSessionManager):
        """
        Initialize the agent RAG service.

        Args:
            session_manager: Session manager for theological agents
        """
        self.session_manager = session_manager
        self.source_formatter = SourceFormatter()

    async def process_query(
        self,
        request: UserQuery,
        session_id: Optional[str] = None
    ) -> AssistantResponse:
        """
        Process a user query through the agent RAG pipeline.

        Args:
            request: User query request
            session_id: Optional session ID for conversation continuity

        Returns:
            Assistant response with answer, sources, conversation history, and session ID

        Raises:
            ValueError: For invalid request parameters
            Exception: For processing errors
        """
        try:
            logger.debug(f"Processing agent RAG query: {request.query}")

            # Get or create session
            session_id, theological_agent = self.session_manager.get_or_create_session(session_id)
            logger.debug(f"Using session: {session_id}")

            # Create callback handler for token tracking
            token_callback = TokenUsageCallbackHandler(endpoint="/query-agent")

            # Query the agent with optional filters (conversation history is maintained in agent memory)
            agent_response = theological_agent.query(
                question=request.query,
                authors=request.authors,
                works=request.works,
                callbacks=[token_callback]
            )

            # Track token usage from the callback
            self._track_token_usage(token_callback)

            # Extract response components
            answer_text = agent_response.get("answer", "")
            agent_sources = agent_response.get("sources", [])

            # Get current conversation history from the agent's memory
            conversation_history = theological_agent.get_conversation_history()

            # Format sources using shared formatter
            formatted_sources = self.source_formatter.format_agent_sources(agent_sources)

            # Log source statistics
            self.source_formatter.log_source_stats(formatted_sources, "agent RAG")

            logger.info(f"Agent successfully processed query with {len(formatted_sources)} sources")

            return AssistantResponse(
                answer=answer_text,
                sources=formatted_sources,
                conversation_history=conversation_history,
                session_id=session_id
            )

        except Exception as e:
            logger.error(f"Error processing agent RAG query: {str(e)}")
            raise

    async def reset_session(self, session_id: str) -> bool:
        """
        Reset a session's conversation memory.

        Args:
            session_id: Session ID to reset

        Returns:
            True if session was reset successfully, False if session not found

        Raises:
            ValueError: If session_id is invalid
        """
        if not session_id:
            raise ValueError("Session ID is required")

        try:
            success = self.session_manager.reset_session(session_id)
            if success:
                logger.info(f"Successfully reset session: {session_id}")
            else:
                logger.warning(f"Session not found for reset: {session_id}")
            return success
        except Exception as e:
            logger.error(f"Error resetting session {session_id}: {str(e)}")
            raise

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session entirely.

        Args:
            session_id: Session ID to delete

        Returns:
            True if session was deleted successfully, False if session not found

        Raises:
            ValueError: If session_id is invalid
        """
        if not session_id:
            raise ValueError("Session ID is required")

        try:
            success = self.session_manager.delete_session(session_id)
            if success:
                logger.info(f"Successfully deleted session: {session_id}")
            else:
                logger.warning(f"Session not found for deletion: {session_id}")
            return success
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            raise

    async def get_session_info(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about sessions.

        Args:
            session_id: Optional specific session ID to get info for

        Returns:
            Session information dictionary

        Raises:
            ValueError: If specific session not found
        """
        try:
            if session_id:
                # Get info for specific session
                session_info = self.session_manager.get_session_info(session_id)
                if session_info:
                    logger.debug(f"Retrieved info for session: {session_id}")
                    return session_info
                else:
                    raise ValueError(f"Session not found: {session_id}")
            else:
                # Get general info about all sessions
                total_sessions = self.session_manager.get_session_count()
                logger.debug(f"Retrieved general session info: {total_sessions} total sessions")
                return {
                    "total_sessions": total_sessions,
                    "message": "Use session_id parameter to get specific session info"
                }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error getting session info: {str(e)}")
            raise

    def get_session_count(self) -> int:
        """
        Get the current number of active sessions.

        Returns:
            Number of active sessions
        """
        try:
            return self.session_manager.get_session_count()
        except Exception as e:
            logger.error(f"Error getting session count: {str(e)}")
            return 0

    def _track_token_usage(self, callback: TokenUsageCallbackHandler):
        """
        Track token usage from the callback handler.

        Args:
            callback: Token usage callback handler with accumulated usage
        """
        try:
            usage = callback.get_total_usage()

            if usage["total_tokens"] > 0:
                tracker = get_token_tracker()
                tracker.record_usage(
                    input_tokens=usage["input_tokens"],
                    output_tokens=usage["output_tokens"],
                    endpoint=usage["endpoint"],
                    model=usage["model"]
                )

                logger.debug(
                    f"Tracked agent token usage: input={usage['input_tokens']}, "
                    f"output={usage['output_tokens']}, calls={usage['call_count']}"
                )
        except Exception as e:
            logger.error(f"Error tracking token usage: {e}")