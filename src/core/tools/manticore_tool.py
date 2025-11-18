"""
LangChain tool for searching the Christian Classics Ethereal Library (CCEL) database
using the Manticore search service.
"""

import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from ...infrastructure.search.manticore import get_paragraphs
from ...models.schemas import UserQuery

logger = logging.getLogger(__name__)


class SearchCCELInput(BaseModel):
    """Input schema for search_ccel_database tool."""
    query: str = Field(description="The theological question or topic to search for")
    authors: str = Field(default="", description="Comma-separated author IDs as plain string (e.g., 'augustine,aquinas' or 'augustine'). Do NOT use JSON array format.")
    works: str = Field(default="", description="Comma-separated work IDs as plain string (e.g., 'confessions,city' or 'holy_wisdom'). Do NOT use JSON array format.")
    top_k: int = Field(default=20, description="Maximum number of results to return (1-20)")


class SourceDetailsInput(BaseModel):
    """Input schema for get_ccel_source_details tool."""
    record_id: str = Field(description="The unique identifier for the CCEL record")


def _search_ccel_database_impl(query: str, authors: str = "", works: str = "", top_k: int = 20) -> str:
    """
    Implementation of CCEL database search.

    Args:
        query: The theological question or topic to search for
        authors: Comma-separated list of author IDs to filter by
        works: Comma-separated list of work IDs to filter by
        top_k: Maximum number of results to return

    Returns:
        Formatted search results with relevant passages and source information
    """
    try:
        logger.debug(f"Searching CCEL database for: {query} (top_k={top_k})")

        # Validate and clamp top_k
        top_k = max(1, min(20, top_k))  # Clamp between 1 and 20

        # Parse comma-separated filters
        authors_filter = [a.strip() for a in authors.split(",") if a.strip()] if authors else []
        works_filter = [w.strip() for w in works.split(",") if w.strip()] if works else []

        # Create UserQuery object with filters
        user_query = UserQuery(
            query=query,
            top_k=top_k,
            authors=authors_filter,
            works=works_filter
        )

        # Log what filters are being applied
        if authors_filter or works_filter:
            logger.info(f"Applying filters - Authors: {authors_filter}, Works: {works_filter}")

        # Get paragraphs from Manticore service
        paragraphs = get_paragraphs(user_query)

        # Handle error case
        if isinstance(paragraphs, dict) and "answer" in paragraphs:
            return f"Search service temporarily unavailable: {paragraphs['answer']}"

        # Format results for the agent
        if not paragraphs or not isinstance(paragraphs, list):
            return "No relevant passages found in the Christian Classics Ethereal Library for this query."

        results_count = len(paragraphs)
        formatted_results = f"Found {results_count} relevant passage(s) from the Christian Classics Ethereal Library"
        formatted_results += f" (requested top {top_k}):\n\n"

        # Add filter information if filters were applied
        if authors_filter or works_filter:
            filter_parts = []
            if authors_filter:
                filter_parts.append(f"Authors: {', '.join(authors_filter)}")
            if works_filter:
                filter_parts.append(f"Works: {', '.join(works_filter)}")
            formatted_results += f"**Search Filters Applied:** {' | '.join(filter_parts)}\n\n"

        for i, paragraph in enumerate(paragraphs, 1):
            if isinstance(paragraph, dict):
                author = paragraph.get('author', 'Unknown Author')
                title = paragraph.get('title', 'Unknown Work')
                text = paragraph.get('text', '')
                record_id = paragraph.get('record_id', '')
            else:
                # Handle case where paragraph is not a dictionary
                author = 'Unknown Author'
                title = 'Unknown Work'
                text = str(paragraph)
                record_id = ''

            formatted_results += f"**Source {i}:**\n"
            formatted_results += f"Author: {author}\n"
            formatted_results += f"Work: {title}\n"
            formatted_results += f"Record ID: {record_id}\n"
            formatted_results += f"Text: {text}\n\n"

        logger.info(f"Retrieved {len(paragraphs)} valid paragraphs for query: {query}")
        return formatted_results

    except Exception as e:
        logger.error(f"Error searching CCEL database: {str(e)}")
        return f"Error occurred while searching the Christian Classics Ethereal Library: {str(e)}"


def _get_ccel_source_details_impl(record_id: str) -> str:
    """
    Implementation of get CCEL source details.

    Args:
        record_id: The unique identifier for the CCEL record

    Returns:
        Detailed information about the source
    """
    try:
        logger.debug(f"Getting source details for record ID: {record_id}")

        # For now, return basic info - this could be expanded to make a specific API call
        return f"Source record ID: {record_id}. For full text access, visit: https://www.ccel.org/ccel/{record_id}"

    except Exception as e:
        logger.error(f"Error getting source details: {str(e)}")
        return f"Error retrieving source details for record {record_id}: {str(e)}"


# Create structured tools with Pydantic schemas for proper parameter parsing
search_ccel_database = StructuredTool.from_function(
    func=_search_ccel_database_impl,
    name="search_ccel_database",
    description="""Searches the Christian Classics Ethereal Library (CCEL) database to find theological and historical Christian texts related to the query.

This tool should be used when the user asks theological questions, wants information about Christian doctrine, church history, biblical commentary, or references from classical Christian authors like Augustine, Aquinas, Calvin, Luther, Chrysostom, etc.

IMPORTANT: You can call this tool MULTIPLE TIMES with different queries or filters to gather comprehensive information. For example:
- First search broadly: query="grace", top_k=10
- Then search with filters: query="grace", authors="augustine", top_k=5
- Then refine further: query="grace and salvation", authors="augustine", works="confessions", top_k=3

You can optionally filter results by specific authors or works. Use the search_ccel_authors and search_ccel_works tools first to find the correct author and work IDs, then pass them to this function.

Each result includes Record ID which you MUST extract for the SOURCES section.""",
    args_schema=SearchCCELInput,
    return_direct=False
)

get_ccel_source_details = StructuredTool.from_function(
    func=_get_ccel_source_details_impl,
    name="get_ccel_source_details",
    description="""Get detailed information about a specific source from the CCEL database using its record ID. Useful for getting more context about a particular work or author mentioned in search results.""",
    args_schema=SourceDetailsInput,
    return_direct=False
)