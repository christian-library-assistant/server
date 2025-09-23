import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Header

from ..models.schemas import UserQuery, AssistantResponse, TestQueryRequest, TestResponse
from ..infrastructure.search.manticore import clean_manticore_response
from ..infrastructure.ai_clients.base import AIClient
from ..core.agents.session_manager import AgentSessionManager
from ..core.services.rag_service import RegularRAGService
from ..core.services.agent_service import AgentRAGService
from ..core.services.test_service import TestService
from ..config.settings import MANTICORE_API_URL, IS_DEVELOPMENT

import requests

logger = logging.getLogger(__name__)
# Only set debug level in development
if IS_DEVELOPMENT:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)

router = APIRouter()


def get_ai_client(request: Request) -> AIClient:
    """Dependency to get the AI client from app state."""
    return request.app.state.anthropic_client


def get_session_manager(request: Request) -> AgentSessionManager:
    """Dependency to get the session manager from app state."""
    if not hasattr(request.app.state, 'session_manager'):
        # Initialize the session manager if it doesn't exist
        request.app.state.session_manager = AgentSessionManager()
    return request.app.state.session_manager


def get_rag_service(ai_client: AIClient = Depends(get_ai_client)) -> RegularRAGService:
    """Dependency to create a RAG service instance."""
    return RegularRAGService(ai_client)


def get_agent_service(session_manager: AgentSessionManager = Depends(get_session_manager)) -> AgentRAGService:
    """Dependency to create an Agent RAG service instance."""
    return AgentRAGService(session_manager)


def get_test_service(
    rag_service: RegularRAGService = Depends(get_rag_service),
    agent_service: AgentRAGService = Depends(get_agent_service)
) -> TestService:
    """Dependency to create a Test service instance."""
    return TestService(rag_service, agent_service)


@router.get("/record-ids")
def record_ids_from_text(request: UserQuery):
    """Get record IDs from text query using Manticore API."""
    try:
        ids = []

        # Send the text as a query parameter
        response = requests.get(MANTICORE_API_URL, params={"text": request.query})
        #logger.debug(f"Manticore response: {response.text}")
        cleaned_response = clean_manticore_response(response.text)

        # Extract IDs
        for item in cleaned_response:
            ids.append(item['record_id'])

        return ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting paragraph ids: {str(e)}")


@router.post("/query")
async def generate_response(
    request: UserQuery,
    rag_service: RegularRAGService = Depends(get_rag_service)
) -> AssistantResponse:
    """Generate a response to user query using AI and context from Manticore."""
    try:
        return await rag_service.process_query(request)
    except ValueError as e:
        logger.warning(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/query-agent")
async def generate_response_with_agent(
    request: UserQuery,
    session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    agent_service: AgentRAGService = Depends(get_agent_service)
) -> AssistantResponse:
    """
    Generate a response to user query using the agentic RAG system.

    This endpoint uses a LangChain agent with Claude that can reason about
    when to search the CCEL database. 
    Helps maintain conversation. 
    Each user gets their own persistent conversation session.
    """
    try:
        # Use session ID from header or request body
        effective_session_id = session_id or request.session_id
        return await agent_service.process_query(request, effective_session_id)
    except ValueError as e:
        logger.warning(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating response with agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/query-agent-reset")
async def reset_agent_conversation(
    session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    agent_service: AgentRAGService = Depends(get_agent_service)
):
    """Reset a specific session's conversation memory."""
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required in X-Session-ID header")

        success = await agent_service.reset_session(session_id)
        if success:
            return {"message": "Agent conversation reset successfully", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="Session not found")

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error resetting agent conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/query-agent-session")
async def delete_agent_session(
    session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    agent_service: AgentRAGService = Depends(get_agent_service)
):
    """Delete a specific session entirely."""
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required in X-Session-ID header")

        success = await agent_service.delete_session(session_id)
        if success:
            return {"message": "Session deleted successfully", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="Session not found")

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/query-agent-sessions")
async def get_session_info(
    session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    agent_service: AgentRAGService = Depends(get_agent_service)
):
    """Get information about sessions."""
    try:
        return await agent_service.get_session_info(session_id)
    except ValueError as e:
        logger.warning(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/test")
async def test_rag_systems(
    request: TestQueryRequest,
    test_service: TestService = Depends(get_test_service)
) -> TestResponse:
    """
    🧪 **TESTING ENDPOINT** - Compare Agentic vs Regular RAG Systems
    
    This endpoint allows you to test both RAG systems without maintaining session state.
    Perfect for experimentation and comparison!
    
    **Parameters:**
    - `query`: Your question/search text
    - `agentic`: `true` for Agentic RAG, `false` for Regular RAG (default: false)
    - `top_k`: Number of results to retrieve (default: 5)
    - `return_fields`: What data to include in results (default: ["record_id"])
    
    **Available return_fields:**
    - `record_id`: Unique identifier for each result
    - `text`: The actual content/paragraph text
    - `authorid`: Author identifier
    - `workid`: Work/book identifier  
    - `versionid`: Version identifier
    - `sectionid`: Section identifier
    - `docid`: Document ID
    - `knn_distance`: Semantic similarity score
    - `refs`: References/citations
    - `link`: URL link to source
    - `citation_text`: Formatted citation
    - `answer`: AI-generated response (only when using agentic mode)
    
    **Examples:**
    ```json
    {
      "query": "What is salvation?",
      "agentic": false,
      "return_fields": ["record_id", "text", "authorid"]
    }
    ```
    
    ```json
    {
      "query": "Explain the Trinity",
      "agentic": true,
      "top_k": 3,
      "return_fields": ["record_id", "text", "answer", "citation_text"]
    }
    ```
    """
    try:
        return await test_service.process_test_query(request)
    except ValueError as e:
        logger.warning(f"Invalid test request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in test endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test endpoint error: {str(e)}")


@router.get("/test/fields")
async def get_test_fields():
    """
    📋 **Get Available Test Fields**
    
    Returns all available fields that can be requested in the test endpoint.
    Use this to discover what data you can include in your test responses.
    """
    return {
        "available_fields": TestService.get_available_fields(),
        "field_descriptions": TestService.get_field_descriptions(),
        "usage_example": {
            "query": "What is the nature of God?",
            "agentic": True,
            "top_k": 5,
            "return_fields": ["record_id", "text", "authorid", "workid", "answer"]
        }
    }