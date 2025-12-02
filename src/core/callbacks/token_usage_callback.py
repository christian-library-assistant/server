"""
Token Usage Callback Handler for LangChain.

This callback handler tracks token usage from LLM calls and records
them using the TokenUsageTracker service.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import BaseMessage

from ...config.settings import IS_DEVELOPMENT

logger = logging.getLogger(__name__)
if IS_DEVELOPMENT:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)


class TokenUsageCallbackHandler(BaseCallbackHandler):
    """
    Callback handler that tracks token usage from LLM calls.

    This handler accumulates token usage across multiple LLM calls
    within an agent execution, then provides methods to retrieve
    the total usage.
    """

    def __init__(self, endpoint: str = "unknown"):
        """
        Initialize the callback handler.

        Args:
            endpoint: The API endpoint making the LLM calls
        """
        super().__init__()
        self.endpoint = endpoint
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0
        self.model_name = "unknown"

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """
        Called when LLM call ends. Extract and accumulate token usage.

        Args:
            response: The LLM result containing generations and metadata
            run_id: Unique identifier for this run
            parent_run_id: Parent run identifier if nested
            **kwargs: Additional keyword arguments
        """
        try:
            self.call_count += 1

            # Try to get token usage from llm_output (standard location)
            if response.llm_output:
                usage = response.llm_output.get("usage", {})
                if usage:
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    self.total_input_tokens += input_tokens
                    self.total_output_tokens += output_tokens

                    logger.debug(
                        f"LLM call #{self.call_count}: "
                        f"input={input_tokens}, output={output_tokens}"
                    )

                # Get model name if available
                if "model_name" in response.llm_output:
                    self.model_name = response.llm_output["model_name"]
                elif "model" in response.llm_output:
                    self.model_name = response.llm_output["model"]

            # Also try to get usage from generation metadata (for some providers)
            for generation_list in response.generations:
                for generation in generation_list:
                    if hasattr(generation, "generation_info") and generation.generation_info:
                        usage = generation.generation_info.get("usage", {})
                        if usage and not response.llm_output:
                            # Only use this if llm_output didn't have usage
                            input_tokens = usage.get("input_tokens", 0)
                            output_tokens = usage.get("output_tokens", 0)
                            self.total_input_tokens += input_tokens
                            self.total_output_tokens += output_tokens

                    # Check message response_metadata for ChatModels
                    if hasattr(generation, "message") and generation.message:
                        msg = generation.message
                        if hasattr(msg, "response_metadata") and msg.response_metadata:
                            usage = msg.response_metadata.get("usage", {})
                            if usage:
                                input_tokens = usage.get("input_tokens", 0)
                                output_tokens = usage.get("output_tokens", 0)
                                # Only add if not already counted from llm_output
                                if not response.llm_output or not response.llm_output.get("usage"):
                                    self.total_input_tokens += input_tokens
                                    self.total_output_tokens += output_tokens

                                logger.debug(
                                    f"From response_metadata: "
                                    f"input={input_tokens}, output={output_tokens}"
                                )

                            # Get model from response_metadata
                            if "model" in msg.response_metadata:
                                self.model_name = msg.response_metadata["model"]

        except Exception as e:
            logger.error(f"Error extracting token usage: {e}")

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM errors."""
        logger.warning(f"LLM error occurred: {error}")

    def get_total_usage(self) -> Dict[str, Any]:
        """
        Get the total accumulated token usage.

        Returns:
            Dictionary with input_tokens, output_tokens, total_tokens,
            call_count, model, and endpoint
        """
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "call_count": self.call_count,
            "model": self.model_name,
            "endpoint": self.endpoint
        }

    def reset(self):
        """Reset the accumulated token counts."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0
        self.model_name = "unknown"
