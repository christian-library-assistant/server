import anthropic
import logging
from typing import List, Dict, Any, Optional

from .base import AIClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AnthropicClient(AIClient):
    """Anthropic Claude AI client implementation."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using the Claude API.

        Args:
            system_prompt: System prompt to guide the model
            user_prompt: User's prompt/query
            conversation_history: Previous conversation history

        Returns:
            Dictionary containing the response and metadata
        """
        messages = []

        # Add conversation history if available
        if conversation_history:
            logger.debug(f"Processing conversation history with {len(conversation_history)} messages")
            for msg in conversation_history:
                if msg["role"] == "user":
                    # Store just the query for user messages, not the full prompt with context
                    user_content = msg["content"]
                    # If the content contains CONTEXT: or QUESTION:, extract just the question
                    if "CONTEXT:" in user_content and "QUESTION:" in user_content:
                        user_content = user_content.split("QUESTION:")[-1].strip()

                    messages.append({"role": "user", "content": user_content})
                    logger.debug(f"Added user message: {user_content[:50]}...")
                else:
                    # Keep assistant messages as they are
                    messages.append(msg)
                    logger.debug(f"Added assistant message: {msg['content'][:50]}...")

        # Add the current user prompt
        messages.append({"role": "user", "content": user_prompt})
        logger.debug(f"Added current user prompt (length: {len(user_prompt)})")

        # Call Claude API to generate response
        logger.debug(f"Calling Claude API with {len(messages)} messages")
        response = self.client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=4000,
            temperature=0.1,
            system=system_prompt,
            messages=messages
        )

        # Extract text from response
        response_text = ""
        if response.content and len(response.content) > 0:
            content_block = response.content[0]
            if hasattr(content_block, 'text'):
                response_text = content_block.text

        logger.debug(f"Claude response received (length: {len(response_text)})")

        # Return response in standard format
        return {
            "content": [{"text": response_text}],
            "metadata": {
                "model": "claude-3-7-sonnet-latest",
                "usage": response.usage.model_dump() if hasattr(response, 'usage') and response.usage else {}
            }
        }