"""
Regular RAG Service for handling standard retrieval-augmented generation queries.

This service extracts the business logic from the /query endpoint and provides
a clean interface for processing user queries with context retrieval.
"""

import logging
from typing import Dict, Any, List, Optional

from ...models.schemas import UserQuery, AssistantResponse
from ...infrastructure.ai_clients.base import AIClient
from ...infrastructure.search.manticore import get_paragraphs
from ...infrastructure.parsers.response_handler import clean_ai_response
from .source_formatter import SourceFormatter
from .token_usage_tracker import get_token_tracker
from ...prompts.system_prompts import get_theological_system_prompt, format_user_prompt

logger = logging.getLogger(__name__)


class RegularRAGService:
    """
    Service for handling regular RAG queries with context retrieval and AI response generation.
    """

    def __init__(self, ai_client: AIClient):
        """
        Initialize the RAG service.

        Args:
            ai_client: AI client for generating responses
        """
        self.ai_client = ai_client
        self.source_formatter = SourceFormatter()

    async def process_query(self, request: UserQuery) -> AssistantResponse:
        """
        Process a user query through the regular RAG pipeline.

        Args:
            request: User query with conversation history

        Returns:
            Assistant response with answer, sources, and updated conversation history

        Raises:
            ValueError: For invalid request parameters
            Exception: For processing errors
        """
        try:
            logger.debug(f"Processing regular RAG query: {request.query}")

            # Fetch context from Manticore
            paragraphs = self._fetch_context(request)
            logger.debug(f"Retrieved {len(paragraphs)} context paragraphs")

            # Prepare prompts
            system_prompt, user_prompt = self._prepare_prompts(
                paragraphs, request.query, request.conversation_history
            )

            # Get AI response
            ai_response = self._get_ai_response(
                system_prompt, user_prompt, request.query, request.conversation_history
            )

            # Track token usage
            self._track_token_usage(ai_response)

            # Process and format the response
            answer_text, formatted_sources = self._process_ai_response(ai_response)

            # Update conversation history
            updated_history = self._update_conversation_history(
                request.conversation_history, request.query, answer_text
            )

            # Log metadata if available
            self._log_response_metadata(ai_response)

            logger.info(f"Successfully processed regular RAG query with {len(formatted_sources)} sources")

            return AssistantResponse(
                answer=answer_text,
                sources=formatted_sources,
                conversation_history=updated_history
            )

        except Exception as e:
            logger.error(f"Error processing regular RAG query: {str(e)}")
            raise

    def _fetch_context(self, request: UserQuery) -> List[Dict[str, Any]]:
        """
        Fetch context paragraphs from Manticore service.

        Args:
            request: User query request

        Returns:
            List of context paragraphs
        """
        try:
            return get_paragraphs(request)
        except Exception as e:
            logger.error(f"Error fetching context: {str(e)}")
            raise Exception(f"Failed to retrieve context: {str(e)}")

    def _prepare_prompts(
        self,
        paragraphs: List[Dict[str, Any]],
        query: str,
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> tuple[str, str]:
        """
        Prepare system and user prompts for AI generation.

        Args:
            paragraphs: Context paragraphs
            query: User query
            conversation_history: Previous conversation

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        try:
            system_prompt = get_theological_system_prompt()

            # Determine if this is a continuation
            is_continuation = len(conversation_history) > 0 if conversation_history else False

            user_prompt = format_user_prompt(paragraphs, query, is_continuation)

            return system_prompt, user_prompt
        except Exception as e:
            logger.error(f"Error preparing prompts: {str(e)}")
            raise Exception(f"Failed to prepare prompts: {str(e)}")

    def _get_ai_response(
        self,
        system_prompt: str,
        user_prompt: str,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> Dict[str, Any]:
        """
        Get response from AI client.

        Args:
            system_prompt: System prompt for AI
            user_prompt: User prompt with context
            user_query: Original user query
            conversation_history: Previous conversation

        Returns:
            AI response dictionary
        """
        try:
            return self.ai_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                user_query=user_query,
                conversation_history=conversation_history
            )
        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}")
            raise Exception(f"AI service error: {str(e)}")

    def _process_ai_response(self, ai_response: Dict[str, Any]) -> tuple[str, List[Dict[str, str]]]:
        """
        Process and format AI response, extracting answer and sources.

        Args:
            ai_response: Raw AI response

        Returns:
            Tuple of (answer_text, formatted_sources)
        """
        try:
            # Check if we have structured data from tool response
            if 'structured_data' in ai_response and ai_response['structured_data']:
                structured_data = ai_response['structured_data']
                answer_text = structured_data.get('answer', '')
                sources = structured_data.get('sources', [])
                logger.debug(f"Using structured data: {len(sources)} sources found")

                formatted_sources = self.source_formatter.format_structured_sources(structured_data)
            else:
                # Fall back to parsing text response
                answer_text, sources, _ = clean_ai_response(ai_response['content'][0]['text'])
                logger.debug(f"Using text parsing: {len(sources)} sources found")

                formatted_sources = self.source_formatter.format_sources(sources)

            # Log source statistics
            self.source_formatter.log_source_stats(formatted_sources, "regular RAG")

            return answer_text, formatted_sources

        except Exception as e:
            logger.error(f"Error processing AI response: {str(e)}")
            raise Exception(f"Failed to process AI response: {str(e)}")

    def _update_conversation_history(
        self,
        conversation_history: Optional[List[Dict[str, str]]],
        query: str,
        answer_text: str
    ) -> List[Dict[str, str]]:
        """
        Update conversation history with current exchange.

        Args:
            conversation_history: Previous conversation history
            query: Current user query
            answer_text: AI response

        Returns:
            Updated conversation history
        """
        try:
            updated_history = conversation_history.copy() if conversation_history else []

            # Add the current exchange to the history
            updated_history.append({"role": "user", "content": query})
            updated_history.append({"role": "assistant", "content": answer_text})

            logger.debug(f"Updated conversation history to {len(updated_history)} messages")

            return updated_history
        except Exception as e:
            logger.error(f"Error updating conversation history: {str(e)}")
            # Return safe fallback
            return [
                {"role": "user", "content": query},
                {"role": "assistant", "content": answer_text}
            ]

    def _track_token_usage(self, ai_response: Dict[str, Any]):
        """
        Track token usage from AI response.

        Args:
            ai_response: AI response containing metadata with usage info
        """
        try:
            metadata = ai_response.get("metadata", {})
            usage = metadata.get("usage", {})

            if usage:
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                model = metadata.get("model", "unknown")

                tracker = get_token_tracker()
                tracker.record_usage(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    endpoint="/query",
                    model=model
                )

                logger.debug(
                    f"Tracked token usage: input={input_tokens}, output={output_tokens}"
                )
        except Exception as e:
            logger.error(f"Error tracking token usage: {e}")

    def _log_response_metadata(self, ai_response: Dict[str, Any]):
        """
        Log response metadata if available.

        Args:
            ai_response: AI response with potential metadata
        """
        try:
            if ai_response.get('metadata') and 'thinking_tokens' in ai_response['metadata']:
                logger.info(f"AI thinking tokens: {ai_response['metadata']['thinking_tokens']}")
        except Exception as e:
            logger.debug(f"Error logging metadata: {str(e)}")  # Non-critical, just debug