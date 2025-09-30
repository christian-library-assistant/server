"""
LangChain tool for searching the Christian Classics Ethereal Library (CCEL) database
using the Manticore search service.
"""

import logging
from typing import List, Optional
from langchain.tools import tool

from ...infrastructure.search.manticore import get_paragraphs
from ...models.schemas import UserQuery

logger = logging.getLogger(__name__)


@tool
def search_ccel_database(query: str, authors: str = "", works: str = "") -> str:
    """
    Searches the Christian Classics Ethereal Library (CCEL) database to find
    theological and historical Christian texts related to the query.

    This tool should be used when the user asks theological questions, wants
    information about Christian doctrine, church history, biblical commentary,
    or references from classical Christian authors like Augustine, Aquinas,
    Calvin, Luther, Chrysostom, etc.

    You can optionally filter results by specific authors or works. Use the
    search_ccel_authors and search_ccel_works tools first to find the correct
    author and work IDs, then pass them to this function.

    Args:
        query: The theological question or topic to search for
        authors: Comma-separated list of author IDs to filter by (e.g., "augustine,aquinas")
        works: Comma-separated list of work IDs to filter by (e.g., "confessions,city")

    Returns:
        Formatted search results with relevant passages and source information
    """
    try:
        logger.debug(f"Searching CCEL database for: {query}")

        # Parse comma-separated filters
        authors_filter = [a.strip() for a in authors.split(",") if a.strip()] if authors else []
        works_filter = [w.strip() for w in works.split(",") if w.strip()] if works else []

        # Create UserQuery object with filters
        user_query = UserQuery(
            query=query,
            top_k=5,
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

        formatted_results = "Found the following relevant passages from the Christian Classics Ethereal Library:\n\n"

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


@tool
def get_ccel_source_details(record_id: str) -> str:
    """
    Get detailed information about a specific source from the CCEL database
    using its record ID. Useful for getting more context about a particular
    work or author mentioned in search results.

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