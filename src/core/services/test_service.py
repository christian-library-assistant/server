"""
Test Service for handling experimental RAG system comparisons.

This service provides a testing interface to compare Agentic vs Regular RAG
without maintaining session state, perfect for experimentation and benchmarking.
"""

import logging
import time
import requests
from typing import Dict, Any, List, Optional

from ...models.schemas import UserQuery, TestQueryRequest, TestResponse
from ...infrastructure.search.manticore import clean_manticore_response
from ...config.settings import MANTICORE_API_URL
from .rag_service import RegularRAGService
from .agent_service import AgentRAGService

logger = logging.getLogger(__name__)


class TestService:
    """
    Service for handling test queries that compare different RAG approaches.
    """

    def __init__(self, rag_service: RegularRAGService, agent_service: AgentRAGService):
        """
        Initialize the test service.

        Args:
            rag_service: Regular RAG service instance
            agent_service: Agentic RAG service instance
        """
        self.rag_service = rag_service
        self.agent_service = agent_service

    async def process_test_query(self, request: TestQueryRequest) -> TestResponse:
        """
        Process a test query using either Agentic or Regular RAG.

        Args:
            request: Test query request with configuration

        Returns:
            Test response with results and processing information

        Raises:
            ValueError: For invalid request parameters
            Exception: For processing errors
        """
        start_time = time.time()
        
        # Validate configuration
        if not MANTICORE_API_URL:
            raise ValueError("MANTICORE_API_URL not configured")
        
        # Create a UserQuery object for processing
        user_query = UserQuery(
            query=request.query,
            top_k=request.top_k,
            conversation_history=[],
            session_id=None  # No session for testing
        )
        
        results = []
        ai_answer = None
        processing_info = {
            "mode": "agentic" if request.agentic else "regular",
            "top_k": request.top_k,
            "requested_fields": request.return_fields
        }
        
        try:
            if request.agentic:
                results, ai_answer, processing_info = await self._process_agentic_query(
                    request, user_query, processing_info
                )
            else:
                results, ai_answer, processing_info = await self._process_regular_query(
                    request, user_query, processing_info
                )
            
            # Add timing info
            end_time = time.time()
            processing_info["processing_time_seconds"] = round(end_time - start_time, 3)
            processing_info["results_returned"] = len(results)
            
            return TestResponse(
                query=request.query,
                agentic_mode=request.agentic,
                results=results,
                ai_answer=ai_answer,
                processing_info=processing_info
            )
            
        except Exception as e:
            logger.error(f"Error in test query processing: {str(e)}")
            raise

    async def _process_agentic_query(
        self, 
        request: TestQueryRequest, 
        user_query: UserQuery, 
        processing_info: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], Optional[str], Dict[str, Any]]:
        """Process query using Agentic RAG."""
        logger.info(f"Processing test query with Agentic RAG: {request.query}")
        
        # Generate a unique test session ID
        test_session_id = f"test-{int(time.time())}"
        
        try:
            # Get response from agentic system
            agentic_response = await self.agent_service.process_query(user_query, test_session_id)
            ai_answer = agentic_response.answer
            
            # Get raw search results for field flexibility
            results = await self._get_formatted_results(request)
            
            # Clean up test session
            await self.agent_service.delete_session(test_session_id)
            
            processing_info["sources_found"] = len(agentic_response.sources) if agentic_response.sources else 0
            processing_info["session_cleaned"] = True
            
            return results, ai_answer, processing_info
            
        except Exception as e:
            logger.error(f"Error in agentic processing: {str(e)}")
            # Fallback to basic manticore search if agent fails
            processing_info["agent_error"] = str(e)
            processing_info["fallback_to_search"] = True
            
            fallback_results = await self._get_fallback_results(request)
            return fallback_results, "Error: Could not generate AI response", processing_info

    async def _process_regular_query(
        self, 
        request: TestQueryRequest, 
        user_query: UserQuery, 
        processing_info: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], Optional[str], Dict[str, Any]]:
        """Process query using Regular RAG."""
        logger.info(f"Processing test query with Regular RAG: {request.query}")
        
        try:
            # Get response from regular RAG
            regular_response = await self.rag_service.process_query(user_query)
            ai_answer = regular_response.answer
            
            # Get formatted results
            results = await self._get_formatted_results(request, ai_answer)
            
            processing_info["sources_found"] = len(regular_response.sources) if regular_response.sources else 0
            
            return results, ai_answer, processing_info
            
        except Exception as e:
            logger.error(f"Error in regular RAG processing: {str(e)}")
            # Fallback to basic search
            processing_info["rag_error"] = str(e)
            processing_info["fallback_to_search"] = True
            
            fallback_results = await self._get_fallback_results(request)
            return fallback_results, "Error: Could not generate AI response", processing_info

    async def _get_formatted_results(
        self, 
        request: TestQueryRequest, 
        ai_answer: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get and format search results based on requested fields."""
        # Ensure MANTICORE_API_URL is not None
        if not MANTICORE_API_URL:
            raise ValueError("MANTICORE_API_URL not configured")
            
        # Get raw search results from Manticore
        manticore_response = requests.get(MANTICORE_API_URL, params={"text": request.query})
        cleaned_response = clean_manticore_response(manticore_response.text)
        
        # Limit to top_k results
        limited_results = cleaned_response[:request.top_k]
        
        results = []
        for item in limited_results:
            result_item = self._format_result_item(item, request.return_fields, ai_answer)
            results.append(result_item)
        
        return results

    async def _get_fallback_results(self, request: TestQueryRequest) -> List[Dict[str, Any]]:
        """Get fallback results when main processing fails."""
        # Ensure MANTICORE_API_URL is not None
        if not MANTICORE_API_URL:
            raise ValueError("MANTICORE_API_URL not configured")
            
        manticore_response = requests.get(MANTICORE_API_URL, params={"text": request.query})
        cleaned_response = clean_manticore_response(manticore_response.text)
        limited_results = cleaned_response[:request.top_k]
        
        results = []
        for item in limited_results:
            result_item = {}
            for field in request.return_fields:
                if field in item:
                    result_item[field] = item[field]
                elif field == "answer":
                    result_item[field] = "Error: Could not generate AI response"
                else:
                    result_item[field] = item.get(field, f"Field '{field}' not available")
            results.append(result_item)
        
        return results

    def _format_result_item(
        self, 
        item: Dict[str, Any], 
        return_fields: List[str], 
        ai_answer: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a single result item based on requested fields."""
        result_item = {}
        
        for field in return_fields:
            if field == "record_id":
                result_item[field] = item.get('record_id', '')
            elif field == "text":
                result_item[field] = item.get('text', '')
            elif field == "authorid":
                result_item[field] = item.get('authorid', '')
            elif field == "workid":
                result_item[field] = item.get('workid', '')
            elif field == "versionid":
                result_item[field] = item.get('versionid', '')
            elif field == "sectionid":
                result_item[field] = item.get('sectionid', '')
            elif field == "docid":
                result_item[field] = item.get('docid', '')
            elif field == "knn_distance":
                result_item[field] = item.get('knn_distance', 0.0)
            elif field == "refs":
                result_item[field] = item.get('refs', [])
            elif field == "link":
                # Generate link from record_id
                record_id = item.get('record_id', '')
                result_item[field] = f"https://ccel.org/ccel/{record_id}" if record_id else ""
            elif field == "citation_text":
                # Generate citation from available data
                author = item.get('authorid', '')
                work = item.get('workid', '')
                result_item[field] = f"{author}, {work}" if author and work else ""
            elif field == "answer":
                result_item[field] = ai_answer if ai_answer else "No AI response available"
            else:
                result_item[field] = f"Unknown field: {field}"
        
        return result_item

    @staticmethod
    def get_available_fields() -> List[str]:
        """Get list of all available fields that can be requested."""
        return [
            "record_id",
            "text", 
            "authorid",
            "workid",
            "versionid",
            "sectionid",
            "docid",
            "knn_distance",
            "refs",
            "link",
            "citation_text",
            "answer"
        ]

    @staticmethod
    def get_field_descriptions() -> Dict[str, str]:
        """Get descriptions for all available fields."""
        return {
            "record_id": "Unique identifier for each result",
            "text": "The actual content/paragraph text",
            "authorid": "Author identifier",
            "workid": "Work/book identifier",
            "versionid": "Version identifier",
            "sectionid": "Section identifier",
            "docid": "Document ID",
            "knn_distance": "Semantic similarity score",
            "refs": "References/citations",
            "link": "URL link to source",
            "citation_text": "Formatted citation",
            "answer": "AI-generated response"
        }