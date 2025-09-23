import anthropic
import logging
from typing import List, Dict, Any, Optional

from .base import AIClient
from ...config.settings import IS_DEVELOPMENT

logger = logging.getLogger(__name__)
# Only set debug level in development
if IS_DEVELOPMENT:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)


class AnthropicClient(AIClient):
    """Anthropic Claude AI client implementation."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using the Claude API.

        Args:
            system_prompt: System prompt to guide the model
            user_prompt: Full prompt with context for the model
            user_query: Clean user query for conversation history
            conversation_history: Previous conversation history

        Returns:
            Dictionary containing the response and metadata
        """
        messages = []

        # Add conversation history if available
        if conversation_history:
            logger.debug(f"Processing conversation history with {len(conversation_history)} messages")
            messages.extend(conversation_history)

        # Add the current user prompt (includes context and query)
        messages.append({"role": "user", "content": user_prompt})
        logger.debug(f"Added current user prompt (length: {len(user_prompt)})")

        # Define tool for structured JSON response
        response_tool = {
            "name": "respond_with_json",
            "description": "Respond with structured JSON containing answer and sources",
            "input_schema": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "The main response text"
                    },
                    "sources": {
                        "type": "array",
                        "description": "Array of source citations",
                        "items": {
                            "type": "object",
                            "properties": {
                                "citation": {
                                    "type": "string",
                                    "description": "Source citation text"
                                },
                                "record_id": {
                                    "type": "string",
                                    "description": "Source record identifier"
                                }
                            },
                            "required": ["citation", "record_id"]
                        }
                    }
                },
                "required": ["answer", "sources"]
            }
        }

        # Call Claude API to generate response
        logger.debug(f"Calling Claude API with {len(messages)} messages")
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.1,
            system=system_prompt,
            messages=messages,
            tools=[response_tool],
            tool_choice={"type": "tool", "name": "respond_with_json"}
        )

        # Extract structured response from tool use
        response_data = {"answer": "", "sources": []}
        response_text = ""

        if response.content and len(response.content) > 0:
            content_block = response.content[0]
            if hasattr(content_block, 'type') and content_block.type == 'tool_use':
                if hasattr(content_block, 'input') and content_block.input:
                    # Handle the input object - convert to dict for easier access
                    try:
                        # Convert input to dict - it's typically a Pydantic model or similar
                        if hasattr(content_block.input, 'model_dump'):
                            # Pydantic model
                            input_dict = content_block.input.model_dump()
                        elif hasattr(content_block.input, 'dict'):
                            # Other dict-like object
                            input_dict = content_block.input.dict()
                        else:
                            # Convert to dict if possible
                            input_dict = dict(content_block.input) if content_block.input else {}

                        answer = input_dict.get('answer', '')
                        sources = input_dict.get('sources', [])

                        response_data = {
                            "answer": answer if isinstance(answer, str) else '',
                            "sources": sources if isinstance(sources, list) else []
                        }
                        response_text = response_data.get('answer', '')

                        logger.debug(f"Extracted structured response: answer={len(response_text)} chars, sources={len(response_data['sources'])}")
                    except Exception as e:
                        logger.error(f"Error extracting structured response: {e}")
                        logger.debug(f"Input type: {type(content_block.input)}, Input: {content_block.input}")
                        response_text = ""

        logger.debug(f"Claude response received (length: {len(response_text)})")

        # Return response in standard format
        return {
            "content": [{"text": response_text}],
            "structured_data": response_data,
            "metadata": {
                "model": "claude-3-5-sonnet-20241022",
                "usage": response.usage.model_dump() if hasattr(response, 'usage') and response.usage else {}
            }
        }