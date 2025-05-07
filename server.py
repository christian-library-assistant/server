import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import logging
from typing import List, Dict, Tuple
from manticore import clean_manticore_response, get_paragraphs
from models import (
    UserQuery,
    AssistantResponse,
    ManticoreResponse
)
from gemini_ai import GeminiAIClient, clean_ai_response, format_user_prompt, get_theological_system_prompt, generate_ccel_url
from constants import GOOGLE_API_KEY, MANTICORE_API_URL

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create FastAPI app
app = FastAPI(title="Smart Library Assistant API", debug=True)

# Initialize Gemini client
gemini_client = GeminiAIClient(api_key=GOOGLE_API_KEY)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

api_link = MANTICORE_API_URL

@app.get("/")
def read_root():
    return {"message": "Smart Library Assistant API"}

@app.get("/record-ids")
def record_ids_from_text(request: UserQuery):
    try:
        ids = []

        # Send the text as a query parameter
        response = requests.get(api_link, params={"text": request.query})
        logger.debug(f"Manticore response: {response.text}")
        cleaned_response = clean_manticore_response(response.text)

        # Extract IDs
        for item in cleaned_response:
            ids.append(item['record_id'])
        
        return ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting paragraph ids: {str(e)}")

def deduplicate_sources(sources: List[Dict]) -> List[Dict]:
    """
    Remove duplicate sources based on record_id.
    
    Args:
        sources: List of source dictionaries with record_id, link, and citation_text
        
    Returns:
        Deduplicated list of sources
    """
    seen_record_ids = set()
    unique_sources = []
    
    for source in sources:
        record_id = source.get("record_id")
        if record_id and record_id not in seen_record_ids:
            seen_record_ids.add(record_id)
            unique_sources.append(source)
            
    return unique_sources

@app.post("/query")
def generate_response(request: UserQuery) -> AssistantResponse:
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
        
        # Get response from Gemini
        gemini_response = gemini_client.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            conversation_history=request.conversation_history
        )
        
        # Parse response from Gemini
        answer_text, sources, source_links = clean_ai_response(gemini_response['content'][0]['text'])
        
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
        if gemini_response.get('metadata') and 'thinking_tokens' in gemini_response['metadata']:
            logger.info(f"Gemini thinking tokens: {gemini_response['metadata']['thinking_tokens']}")
        
        return AssistantResponse(
            answer=answer_text,
            sources=formatted_sources,
            conversation_history=updated_history
        )
    except Exception as e:
        logger.error(f"Error generating response from server: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@app.get("/health/")
def health_check():
    return {"message": "Server is running"}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)