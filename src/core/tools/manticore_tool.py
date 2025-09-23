"""
LangChain tool for searching the Christian Classics Ethereal Library (CCEL) database
using the Manticore search service.
"""

import logging
from langchain.tools import tool

from ...infrastructure.search.manticore import get_paragraphs
from ...models.schemas import UserQuery

logger = logging.getLogger(__name__)


@tool
def search_ccel_database(query: str) -> str:
    """
    Searches the Christian Classics Ethereal Library (CCEL) database to find
    theological and historical Christian texts related to the query.

    This tool should be used when the user asks theological questions, wants
    information about Christian doctrine, church history, biblical commentary,
    or references from classical Christian authors like Augustine, Aquinas,
    Calvin, Luther, Chrysostom, etc.

    Args:
        query: The theological question or topic to search for

    Returns:
        Formatted search results with relevant passages and source information
    """
    try:
        logger.debug(f"Searching CCEL database for: {query}")

        # Create UserQuery object for the existing service
        user_query = UserQuery(query=query, top_k=5)

        # Get paragraphs from Manticore service
        paragraphs = get_paragraphs(user_query)

        # Handle error case
        if isinstance(paragraphs, dict) and "answer" in paragraphs:
            return f"Search service temporarily unavailable: {paragraphs['answer']}"

        # Format results for the agent
        if not paragraphs or not isinstance(paragraphs, list):
            return "No relevant passages found in the Christian Classics Ethereal Library for this query."

        formatted_results = "Found the following relevant passages from the Christian Classics Ethereal Library:\n\n"

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

        logger.debug(f"Successfully retrieved {len(paragraphs)} passages from CCEL")
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