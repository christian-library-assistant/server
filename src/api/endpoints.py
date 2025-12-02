import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Header

from ..models.schemas import UserQuery, AssistantResponse, TestQueryRequest, TestResponse
from ..infrastructure.search.manticore import (
    clean_manticore_response,
    get_all_authors,
    get_all_works,
    search_authors_semantic,
    search_works_semantic
)
from ..infrastructure.ai_clients.base import AIClient
from ..core.agents.session_manager import AgentSessionManager
from ..core.services.rag_service import RegularRAGService
from ..core.services.agent_service import AgentRAGService
from ..core.services.test_service import TestService
from ..core.services.token_usage_tracker import get_token_tracker
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

    **Filtering by Author or Work:**
    You can limit searches to specific authors or works by including them in the request:
    ```json
    {
      "query": "What is grace?",
      "authors": ["augustine"],
      "works": ["confessions"]
    }
    ```

    When filters are provided, the agent will be instructed to ONLY search within those
    specific authors/works. This is different from mentioning an author in the query text -
    filters are enforced constraints that apply to all searches during the session.

    **Discovering Author/Work IDs:**
    - GET /authors - List all available author IDs
    - GET /authors?query=augustine - Search for author IDs
    - GET /works - List all available work IDs
    - GET /works?query=confessions - Search for work IDs
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
            # Return success for non-existent sessions (idempotent operation)
            # Sessions are only created when first query is sent
            return {
                "message": "Session reset successful (session did not exist or already empty)",
                "session_id": session_id,
                "note": "Sessions are created when you send your first query"
            }

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
            # Return success for non-existent sessions (idempotent operation)
            # Sessions are only created when first query is sent
            return {
                "message": "Session deletion successful (session did not exist)",
                "session_id": session_id,
                "note": "Sessions are created when you send your first query"
            }

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
        # Return a helpful message instead of 404 for non-existent sessions
        return {
            "exists": False,
            "message": "Session not found or has expired. Sessions expire after 30 minutes of inactivity.",
            "session_id": session_id
        }
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


@router.get("/authors")
async def search_authors(query: Optional[str] = None):
    """
    🔍 **Search or List Authors**

    Discover valid author IDs for filtering searches.

    **Without query parameter:** Returns all author IDs from the CCEL database.

    **With query parameter:** Performs semantic search using AI embeddings to find matching authors.

    **Examples:**
    - `GET /authors` - Returns all authors
    - `GET /authors?query=augustine` - Searches for authors matching "augustine"
    - `GET /authors?query=early church father` - Searches semantically for early church fathers

    **Use these IDs with:**
    - `/query-agent` endpoint's `authors` parameter
    - `/test` endpoint's `authors` parameter
    """
    try:
        # If no query, return all authors
        if not query:
            authors_data = get_all_authors()

            # Handle error case
            if isinstance(authors_data, dict) and "error" in authors_data:
                raise HTTPException(status_code=503, detail=authors_data["error"])

            if not isinstance(authors_data, list):
                raise HTTPException(status_code=500, detail="Invalid response from authors service")

            return {
                "total": len(authors_data),
                "authors": sorted(authors_data),
                "note": "Use query parameter to search: GET /authors?query=augustine"
            }

        # Perform semantic search
        authors_data = search_authors_semantic(query)

        # Handle error case
        if isinstance(authors_data, dict) and "error" in authors_data:
            raise HTTPException(status_code=503, detail=authors_data["error"])

        if not isinstance(authors_data, dict):
            raise HTTPException(status_code=500, detail="Invalid response from authors search service")

        if len(authors_data) == 0:
            return {
                "query": query,
                "total_matches": 0,
                "matches": [],
                "message": f"No authors found matching '{query}'"
            }

        # Format results with author info
        # API returns: {"authorid": {"authorname": "Name", "associatedworks": {"workid": "workname", ...}}, ...}
        formatted_matches = []
        for author_id, author_info in authors_data.items():
            author_name = author_info.get('authorname', author_id)
            associated_works = author_info.get('associatedworks', {})

            formatted_matches.append({
                "author_id": author_id,
                "author_name": author_name,
                "associated_works": associated_works
            })

        return {
            "query": query,
            "total_matches": len(formatted_matches),
            "matches": formatted_matches,
            "usage_example": {
                "endpoint": "/query-agent",
                "request_body": {
                    "query": "What is grace?",
                    "authors": [formatted_matches[0]["author_id"]] if formatted_matches else []
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching authors: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching authors: {str(e)}")


@router.get("/works")
async def search_works(query: Optional[str] = None):
    """
    📚 **Search or List Works**

    Discover valid work IDs for filtering searches.

    **Without query parameter:** Returns all work IDs from the CCEL database.

    **With query parameter:** Performs semantic search using AI embeddings to find matching works.

    **Examples:**
    - `GET /works` - Returns all works
    - `GET /works?query=confessions` - Searches for works matching "confessions"
    - `GET /works?query=book about prayer` - Searches semantically for works about prayer

    **Use these IDs with:**
    - `/query-agent` endpoint's `works` parameter
    - `/test` endpoint's `works` parameter
    """
    try:
        # If no query, return all works
        if not query:
            works_data = get_all_works()

            # Handle error case
            if isinstance(works_data, dict) and "error" in works_data:
                raise HTTPException(status_code=503, detail=works_data["error"])

            if not isinstance(works_data, list):
                raise HTTPException(status_code=500, detail="Invalid response from works service")

            return {
                "total": len(works_data),
                "works": sorted(works_data),
                "note": "Use query parameter to search: GET /works?query=confessions"
            }

        # Perform semantic search
        works_data = search_works_semantic(query)

        # Handle error case
        if isinstance(works_data, dict) and "error" in works_data:
            raise HTTPException(status_code=503, detail=works_data["error"])

        if not isinstance(works_data, list):
            raise HTTPException(status_code=500, detail="Invalid response from works search service")

        if len(works_data) == 0:
            return {
                "query": query,
                "total_matches": 0,
                "matches": [],
                "message": f"No works found matching '{query}'"
            }

        # Format results with work info
        # API returns: [{"authorid": "...", "authorname": "...", "workid": "...", "workname": "..."}, ...]
        # Group works by unique work IDs to avoid duplicates
        seen_works = {}
        for item in works_data:
            work_id = item.get('workid', '')
            work_name = item.get('workname', work_id)
            author_id = item.get('authorid', '')
            author_name = item.get('authorname', author_id)

            if work_id not in seen_works:
                seen_works[work_id] = {
                    'work_name': work_name,
                    'authors': [{
                        'author_id': author_id,
                        'author_name': author_name
                    }]
                }
            else:
                # Check if author already in list
                if not any(a['author_id'] == author_id for a in seen_works[work_id]['authors']):
                    seen_works[work_id]['authors'].append({
                        'author_id': author_id,
                        'author_name': author_name
                    })

        formatted_matches = [
            {
                "work_id": work_id,
                "work_name": work_info['work_name'],
                "authors": work_info['authors']
            }
            for work_id, work_info in seen_works.items()
        ]

        return {
            "query": query,
            "total_matches": len(formatted_matches),
            "matches": formatted_matches,
            "usage_example": {
                "endpoint": "/query-agent",
                "request_body": {
                    "query": "What is grace?",
                    "works": [formatted_matches[0]["work_id"]] if formatted_matches else []
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching works: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching works: {str(e)}")


# ============================================================================
# Token Usage Statistics Endpoints
# ============================================================================

@router.get("/stats/usage")
async def get_token_usage_summary(days: int = 30):
    """
    📊 **Get Token Usage Summary**

    Returns aggregated token usage statistics for the specified period.

    **Parameters:**
    - `days`: Number of days to include in summary (default: 30, max: 365)

    **Response includes:**
    - Total input/output tokens
    - Breakdown by endpoint (/query, /query-agent)
    - Breakdown by model
    - Daily averages

    **Examples:**
    - `GET /stats/usage` - Last 30 days summary
    - `GET /stats/usage?days=7` - Last 7 days summary
    """
    try:
        # Validate days parameter
        if days < 1:
            days = 1
        elif days > 365:
            days = 365

        tracker = get_token_tracker()
        summary = tracker.get_usage_summary(days=days)

        return {
            "status": "success",
            "data": summary
        }

    except Exception as e:
        logger.error(f"Error getting token usage summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting usage statistics: {str(e)}")


@router.get("/stats/usage/daily")
async def get_daily_token_usage(days: int = 30):
    """
    📈 **Get Daily Token Usage Breakdown**

    Returns day-by-day token usage for the specified period.

    **Parameters:**
    - `days`: Number of days to include (default: 30, max: 90)

    **Response includes:**
    - Daily input/output tokens
    - Daily request counts
    - Per-endpoint breakdown for each day

    **Examples:**
    - `GET /stats/usage/daily` - Last 30 days daily breakdown
    - `GET /stats/usage/daily?days=7` - Last 7 days daily breakdown
    """
    try:
        # Validate days parameter
        if days < 1:
            days = 1
        elif days > 90:
            days = 90

        tracker = get_token_tracker()
        daily_data = tracker.get_daily_breakdown(days=days)

        return {
            "status": "success",
            "days_requested": days,
            "data": daily_data
        }

    except Exception as e:
        logger.error(f"Error getting daily token usage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting daily statistics: {str(e)}")


@router.get("/stats/usage/today")
async def get_today_token_usage():
    """
    📅 **Get Today's Token Usage**

    Returns token usage statistics for today only.

    **Response includes:**
    - Today's input/output tokens
    - Request count
    - Per-endpoint breakdown
    """
    try:
        tracker = get_token_tracker()
        today_data = tracker.get_today_usage()

        return {
            "status": "success",
            "data": today_data
        }

    except Exception as e:
        logger.error(f"Error getting today's token usage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting today's statistics: {str(e)}")