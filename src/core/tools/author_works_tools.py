"""
LangChain tools for searching authors and works in the CCEL database.
"""

import logging
from typing import List, Dict, Any
from langchain.tools import tool

from ...infrastructure.search.manticore import search_authors_semantic, search_works_semantic

logger = logging.getLogger(__name__)


@tool
def search_ccel_authors(query: str) -> str:
    """
    Search for authors in the Christian Classics Ethereal Library (CCEL) database using semantic search.
    Uses AI embeddings to find authors most similar to the query, understanding meaning not just text similarity.
    Returns matching authors with their IDs, names, and associated works.
    Use this when the user mentions an author name to find the exact author ID for filtering searches.

    Args:
        query: Author name or description to search for (e.g., "Augustine", "Aquinas", "Luther", "early church father")

    Returns:
        Matching authors with their IDs, names, and associated works
    """
    try:
        logger.debug(f"Performing semantic search for CCEL authors: {query}")

        # Use semantic search API
        authors_data = search_authors_semantic(query)

        # Handle error case
        if isinstance(authors_data, dict) and "error" in authors_data:
            return f"Error retrieving authors: {authors_data['error']}"

        if not isinstance(authors_data, dict) or len(authors_data) == 0:
            return f"No authors found matching '{query}' in the CCEL database."

        # Format results with author IDs, names, and associated works
        # API returns: {"authorid": {"authorname": "Name", "associatedworks": {"workid": "workname", ...}}, ...}
        result = f"Authors matching '{query}':\n\n"

        for i, (author_id, author_info) in enumerate(authors_data.items(), 1):
            author_name = author_info.get('authorname', author_id)
            associated_works = author_info.get('associatedworks', {})

            result += f"{i}. {author_name} (ID: {author_id})\n"

            if associated_works:
                result += f"   Associated works: {', '.join(associated_works.values())}\n"

            result += "\n"

        result += "To filter search results by these authors, use their IDs with the search_ccel_database tool."

        return result

    except Exception as e:
        logger.error(f"Error searching CCEL authors: {str(e)}")
        return f"Error occurred while searching authors: {str(e)}"


@tool
def search_ccel_works(query: str) -> str:
    """
    Search for works/titles in the Christian Classics Ethereal Library (CCEL) database using semantic search.
    Uses AI embeddings to find works most similar to the query, understanding meaning not just text similarity.
    Returns matching works with their IDs, names, and associated authors.
    Use this when the user mentions a specific book or work title to find the exact work ID for filtering searches.

    Args:
        query: Work title or description to search for (e.g., "Confessions", "City of God", "Institutes", "book about prayer")

    Returns:
        Matching works with their IDs, names, and associated authors
    """
    try:
        logger.debug(f"Performing semantic search for CCEL works: {query}")

        # Use semantic search API
        works_data = search_works_semantic(query)

        # Handle error case
        if isinstance(works_data, dict) and "error" in works_data:
            return f"Error retrieving works: {works_data['error']}"

        if not isinstance(works_data, list) or len(works_data) == 0:
            return f"No works found matching '{query}' in the CCEL database."

        # Format results with work IDs, names, and authors
        # API returns: [{"authorid": "...", "authorname": "...", "workid": "...", "workname": "..."}, ...]
        result = f"Works matching '{query}':\n\n"

        # Group works by unique work IDs to avoid duplicates
        seen_works = {}
        for item in works_data:
            work_id = item.get('workid', '')
            work_name = item.get('workname', work_id)
            author_name = item.get('authorname', item.get('authorid', 'Unknown'))

            if work_id not in seen_works:
                seen_works[work_id] = {
                    'name': work_name,
                    'authors': [author_name]
                }
            else:
                if author_name not in seen_works[work_id]['authors']:
                    seen_works[work_id]['authors'].append(author_name)

        for i, (work_id, work_info) in enumerate(seen_works.items(), 1):
            work_name = work_info['name']
            authors = ', '.join(work_info['authors'])

            result += f"{i}. {work_name} (ID: {work_id})\n"
            result += f"   By: {authors}\n\n"

        result += "To filter search results by these works, use their IDs with the search_ccel_database tool."

        return result

    except Exception as e:
        logger.error(f"Error searching CCEL works: {str(e)}")
        return f"Error occurred while searching works: {str(e)}"


