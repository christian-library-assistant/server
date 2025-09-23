from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class AIClient(ABC):
    """Abstract base class for AI clients."""

    def __init__(self, api_key: str):
        """Initialize the AI client with an API key."""
        self.api_key = api_key

    @abstractmethod
    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using the AI model.

        Args:
            system_prompt: System prompt to guide the model
            user_prompt: Full prompt with context for the model
            user_query: Clean user query for conversation history
            conversation_history: Previous conversation history

        Returns:
            Dictionary containing the response and metadata
        """
        pass