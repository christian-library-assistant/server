"""
LangChain tools for searching authors and works in the CCEL database.
"""

import logging
from typing import List, Dict, Any
from langchain.tools import tool
from rapidfuzz import process, fuzz

from ...infrastructure.search.manticore import get_all_authors, get_all_works

logger = logging.getLogger(__name__)


@tool
def search_ccel_authors(query: str) -> str:
    """
    Search for authors in the Christian Classics Ethereal Library (CCEL) database using fuzzy matching.
    Returns the top 5 best matches for the given author name or partial name.
    Use this when the user mentions an author name to find the exact author ID for filtering searches.

    Args:
        query: Author name or partial name to search for (e.g., "Augustine", "Aquinas", "Luther")

    Returns:
        Top 5 matching authors with their IDs and similarity scores
    """
    try:
        logger.debug(f"Fuzzy searching CCEL authors for: {query}")

        # Get all authors from the API
        authors_data = get_all_authors()

        # Handle error case
        if isinstance(authors_data, dict) and "error" in authors_data:
            return f"Error retrieving authors: {authors_data['error']}"

        if not isinstance(authors_data, list) or len(authors_data) == 0:
            return "No authors data available"

        # Prepare author list for fuzzy matching
        # Authors are simple strings (authorid values)
        author_list = [str(author) for author in authors_data if author]

        if not author_list:
            return "No valid authors found in database"

        # Use fuzzy matching to find top 5 matches
        matches = process.extract(
            query,
            author_list,
            scorer=fuzz.WRatio,
            limit=5
        )

        if not matches:
            return f"No authors found matching '{query}' in the CCEL database."

        # Format results with author IDs
        result = f"Top 5 author matches for '{query}':\n\n"
        for i, (author_id, score, _) in enumerate(matches, 1):
            result += f"{i}. {author_id} (match: {score}%)\n"

        result += f"\nTo filter search results by these authors, use their IDs with the search_ccel_database tool."

        return result

    except Exception as e:
        logger.error(f"Error searching CCEL authors: {str(e)}")
        return f"Error occurred while searching authors: {str(e)}"


@tool
def search_ccel_works(query: str) -> str:
    """
    Search for works/titles in the Christian Classics Ethereal Library (CCEL) database using fuzzy matching.
    Returns the top 5 best matches for the given work title or partial title.
    Use this when the user mentions a specific book or work title to find the exact work ID for filtering searches.

    Args:
        query: Work title or partial title to search for (e.g., "Confessions", "City of God", "Institutes")

    Returns:
        Top 5 matching works with their IDs and similarity scores
    """
    try:
        logger.debug(f"Fuzzy searching CCEL works for: {query}")

        # Get all works from the API
        works_data = get_all_works()

        # Handle error case
        if isinstance(works_data, dict) and "error" in works_data:
            return f"Error retrieving works: {works_data['error']}"

        if not isinstance(works_data, list) or len(works_data) == 0:
            return "No works data available"

        # Prepare work list for fuzzy matching
        # Works are simple strings (workid values)
        work_list = [str(work) for work in works_data if work]

        if not work_list:
            return "No valid works found in database"

        # Use fuzzy matching to find top 5 matches
        matches = process.extract(
            query,
            work_list,
            scorer=fuzz.WRatio,
            limit=5
        )

        if not matches:
            return f"No works found matching '{query}' in the CCEL database."

        # Format results with work IDs
        result = f"Top 5 work matches for '{query}':\n\n"
        for i, (work_id, score, _) in enumerate(matches, 1):
            result += f"{i}. {work_id} (match: {score}%)\n"

        result += f"\nTo filter search results by these works, use their IDs with the search_ccel_database tool."

        return result

    except Exception as e:
        logger.error(f"Error searching CCEL works: {str(e)}")
        return f"Error occurred while searching works: {str(e)}"


