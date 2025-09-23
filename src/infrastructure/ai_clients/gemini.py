# Copyright 2025 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import List, Dict, Any, Optional

from google import genai
from google.genai import types

from .base import AIClient
from ...config.settings import IS_DEVELOPMENT

logger = logging.getLogger(__name__)
# Only set debug level in development
if IS_DEVELOPMENT:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)


class GeminiClient(AIClient):
    """Google Gemini AI client implementation."""

    def __init__(self, api_key: str, model_id: str = "gemini-2.5-flash"):
        """
        Initialize the Gemini AI client.

        Args:
            api_key: API key for authentication
            model_id: Gemini model ID to use
        """
        super().__init__(api_key)
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        thinking_budget: int = 5000
    ) -> Dict[str, Any]:
        """
        Generate a response using Gemini models with thinking capabilities.

        Args:
            system_prompt: System prompt to guide the model
            user_prompt: Full prompt with context for the model
            user_query: Clean user query for conversation history
            conversation_history: Previous conversation history
            thinking_budget: Token budget for thinking process

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

                    messages.append(types.Part(text=user_content))
                    logger.debug(f"Added user message: {user_content[:50]}...")
                else:
                    # Keep assistant messages as they are
                    messages.append(types.Part(text=msg["content"]))
                    logger.debug(f"Added assistant message: {msg['content'][:50]}...")

        # Add the current user prompt
        messages.append(types.Part(text=user_prompt))
        logger.debug(f"Added current user prompt (length: {len(user_prompt)})")

        # Configure generation parameters
        generation_config = types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=4000
        )

        # Configure thinking if available
        thinking_config = None
        if hasattr(types, 'ThinkingConfig'):
            thinking_config = types.ThinkingConfig(thinking_budget=thinking_budget)

        # Create request
        request_args = {
            "model": self.model_id,
            "contents": [types.Content(parts=messages, role="user")],
            "system_instruction": system_prompt,
            "config": generation_config
        }

        if thinking_config:
            request_args["thinking_config"] = thinking_config

        # Call Gemini API
        logger.debug(f"Calling Gemini API with model {self.model_id}")
        response = self.client.models.generate_content(**request_args)

        logger.debug(f"Gemini response received")

        # Extract response text
        response_text = ""
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                response_text = candidate.content.parts[0].text

        # Extract metadata
        metadata = {
            "model": self.model_id,
            "usage": {}
        }

        # Add thinking tokens if available
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            if hasattr(response.usage_metadata, 'cached_content_token_count'):
                metadata["thinking_tokens"] = response.usage_metadata.cached_content_token_count

        logger.debug(f"Gemini response processed (length: {len(response_text)})")

        # Return response in standard format
        return {
            "content": [{"text": response_text}],
            "metadata": metadata
        }