import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Request

from ..models.schemas import UserQuery, AssistantResponse
from ..services.manticore import get_paragraphs, clean_manticore_response
from ..services.response_handler import clean_ai_response, generate_ccel_url, deduplicate_sources
from ..prompts.prompts import get_theological_system_prompt, format_user_prompt
from ..ai.base import AIClient
from ..config.settings import MANTICORE_API_URL

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = APIRouter()


def get_ai_client(request: Request) -> AIClient:
    """Dependency to get the AI client from app state."""
    return request.app.state.gemini_client


@router.get("/record-ids")
def record_ids_from_text(request: UserQuery):
    """Get record IDs from text query using Manticore API."""
    try:
        ids = []

        # Send the text as a query parameter
        response = requests.get(MANTICORE_API_URL, params={"text": request.query})
        logger.debug(f"Manticore response: {response.text}")
        cleaned_response = clean_manticore_response(response.text)

        # Extract IDs
        for item in cleaned_response:
            ids.append(item['record_id'])

        return ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting paragraph ids: {str(e)}")


@router.post("/query")
def generate_response(request: UserQuery, ai_client: AIClient = Depends(get_ai_client)) -> AssistantResponse:
    """Generate a response to user query using AI and context from Manticore."""
    try:
        # Get paragraph texts from the endpoint
        paragraphs = get_paragraphs(request)

        # Get system prompt
        system_prompt = get_theological_system_prompt()

        # Log the incoming conversation history
        logger.debug(f"Received conversation history with {len(request.conversation_history)} messages")

        # Determine if this is a new conversation or a continuation
        is_continuation = len(request.conversation_history) > 0

        # Format the user prompt with context
        user_prompt = format_user_prompt(paragraphs, request.query, is_continuation)

        # Get response from AI
        ai_response = ai_client.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            conversation_history=request.conversation_history
        )

        # Parse response from AI
        answer_text, sources, source_links = clean_ai_response(ai_response['content'][0]['text'])

        # Create formatted citations with links
        formatted_sources = []

        # Process sources (each source should have citation and record_id)
        for source in sources:
            record_id = source.get("record_id", "")
            citation_text = source.get("citation", "")

            link = generate_ccel_url(record_id)
            if link:
                formatted_sources.append({
                    "record_id": record_id,
                    "link": link,
                    "citation_text": citation_text
                })

        # Remove duplicate sources
        formatted_sources = deduplicate_sources(formatted_sources)

        logger.debug(f"Formatted {len(formatted_sources)} unique sources with citation texts")

        # Create updated conversation history
        updated_history = request.conversation_history.copy() if request.conversation_history else []

        # Add the current exchange to the history
        updated_history.append({"role": "user", "content": request.query})
        updated_history.append({"role": "assistant", "content": answer_text})

        # Log the updated conversation history and source links
        logger.debug(f"Returning updated conversation history with {len(updated_history)} messages")
        logger.debug(f"Returning {len(formatted_sources)} formatted sources after deduplication")

        # Log thinking tokens if available
        if ai_response.get('metadata') and 'thinking_tokens' in ai_response['metadata']:
            logger.info(f"AI thinking tokens: {ai_response['metadata']['thinking_tokens']}")

        return AssistantResponse(
            answer=answer_text,
            sources=formatted_sources,
            conversation_history=updated_history
        )
    except Exception as e:
        logger.error(f"Error generating response from server: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")