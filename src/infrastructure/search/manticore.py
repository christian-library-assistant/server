import json
import requests
import logging
from typing import List, Dict, Any, Union, Optional
from urllib.parse import urlencode

from ...config.settings import MANTICORE_API_URL
from ...models.schemas import UserQuery

logger = logging.getLogger(__name__)


def get_all_works() -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Get all works from the Manticore works endpoint.

    Returns:
        List of work dictionaries or error dictionary if the request fails
    """
    try:
        if not MANTICORE_API_URL:
            logger.error("MANTICORE_API_URL is not configured")
            return {"error": "Search service is not configured. Please contact administrator."}

        # Replace classify.php with works.php in the URL
        base_url = MANTICORE_API_URL.replace('/classify.php', '')
        works_url = f"{base_url}/works.php"

        logger.debug(f"Fetching all works from: {works_url}")
        response = requests.get(works_url, timeout=10)
        response.raise_for_status()

        try:
            works_data = response.json()
            logger.info(f"Successfully retrieved {len(works_data)} works")
            return works_data
        except json.JSONDecodeError:
            logger.error("Failed to parse works response as JSON")
            return {"error": "Invalid response format from works endpoint"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching works: {e}")
        return {"error": f"Failed to fetch works: {str(e)}"}


def search_works_semantic(work_query: str) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Perform semantic search for works using the Manticore API's vector search.
    Uses OpenAI embeddings to find works similar to the query.

    Args:
        work_query: Work title or description to search for

    Returns:
        List of dictionaries containing author-work pairings with IDs and names,
        or error dictionary if the request fails
    """
    try:
        if not MANTICORE_API_URL:
            logger.error("MANTICORE_API_URL is not configured")
            return {"error": "Search service is not configured. Please contact administrator."}

        # Replace classify.php with works.php in the URL
        base_url = MANTICORE_API_URL.replace('/classify.php', '')
        works_url = f"{base_url}/works.php"

        # Add work query parameter for semantic search
        params = {"work": work_query}

        logger.debug(f"Performing semantic search for work: {work_query}")
        response = requests.get(works_url, params=params, timeout=10)
        response.raise_for_status()

        try:
            works_data = response.json()
            logger.info(f"Successfully retrieved {len(works_data)} work matches for query: {work_query}")
            return works_data
        except json.JSONDecodeError:
            logger.error("Failed to parse works response as JSON")
            return {"error": "Invalid response format from works endpoint"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching works: {e}")
        return {"error": f"Failed to search works: {str(e)}"}


def get_all_authors() -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Get all authors from the Manticore authors endpoint.

    Returns:
        List of author dictionaries or error dictionary if the request fails
    """
    try:
        if not MANTICORE_API_URL:
            logger.error("MANTICORE_API_URL is not configured")
            return {"error": "Search service is not configured. Please contact administrator."}

        # Replace classify.php with authors.php in the URL
        base_url = MANTICORE_API_URL.replace('/classify.php', '')
        authors_url = f"{base_url}/authors.php"

        logger.debug(f"Fetching all authors from: {authors_url}")
        response = requests.get(authors_url, timeout=10)
        response.raise_for_status()

        try:
            authors_data = response.json()
            logger.info(f"Successfully retrieved {len(authors_data)} authors")
            return authors_data
        except json.JSONDecodeError:
            logger.error("Failed to parse authors response as JSON")
            return {"error": "Invalid response format from authors endpoint"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching authors: {e}")
        return {"error": f"Failed to fetch authors: {str(e)}"}


def search_authors_semantic(author_query: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Perform semantic search for authors using the Manticore API's vector search.
    Uses OpenAI embeddings to find authors similar to the query.

    Args:
        author_query: Author name or description to search for

    Returns:
        Dictionary mapping author IDs to author info (name and associated works),
        or error dictionary if the request fails
    """
    try:
        if not MANTICORE_API_URL:
            logger.error("MANTICORE_API_URL is not configured")
            return {"error": "Search service is not configured. Please contact administrator."}

        # Replace classify.php with authors.php in the URL
        base_url = MANTICORE_API_URL.replace('/classify.php', '')
        authors_url = f"{base_url}/authors.php"

        # Add author query parameter for semantic search
        params = {"author": author_query}

        logger.debug(f"Performing semantic search for author: {author_query}")
        response = requests.get(authors_url, params=params, timeout=10)
        response.raise_for_status()

        try:
            authors_data = response.json()
            logger.info(f"Successfully retrieved {len(authors_data)} author matches for query: {author_query}")
            return authors_data
        except json.JSONDecodeError:
            logger.error("Failed to parse authors response as JSON")
            return {"error": "Invalid response format from authors endpoint"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching authors: {e}")
        return {"error": f"Failed to search authors: {str(e)}"}


def clean_manticore_response(response_text: str) -> List[Dict[str, Any]]:
    """
    Clean and parse response from Manticore search service.

    Args:
        response_text: Raw response text from Manticore API

    Returns:
        List of parsed response items

    Raises:
        json.JSONDecodeError: If response cannot be parsed as JSON
        ValueError: If response format is invalid
    """
    try:
        raw_response = response_text
        
        json_start = raw_response.find('[')
        logger.debug(f"Raw response starts with: {raw_response[:100]}...")
        json_end = raw_response.rfind(']') + 1
        logger.debug(f"JSON segment from {json_start} to {json_end}")

        if json_start == -1 or json_end == 0:
            logger.error(f"Invalid response format: {response_text[:100]}...")
            raise ValueError("Response does not contain valid JSON array")

        json_response = raw_response[json_start:json_end]
        parsed_response = json.loads(json_response)

        if not isinstance(parsed_response, list):
            logger.error(f"Expected list response, got {type(parsed_response)}")
            raise ValueError("Response is not a JSON array")

        return parsed_response
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing response: {e}")
        raise


def get_paragraphs(request: UserQuery) -> Union[List[Dict[str, str]], Dict[str, str]]:
    """
    Get paragraphs from Manticore API for a given query.

    Args:
        request: UserQuery containing the search query, and optionally works and authors filters

    Returns:
        List of paragraph dictionaries containing text and metadata,
        or error dictionary if the request fails
    """
    try:
        if not MANTICORE_API_URL:
            logger.error("MANTICORE_API_URL is not configured")
            return {
                "answer": "Search service is not configured. Please contact administrator.",
            }

        # Build query parameters
        params = {
            "text": request.query,
            "returnLimit": request.top_k or 5
        }

        # Build array parameters for works[] and authors[]
        work_params = []
        if hasattr(request, 'works') and request.works:
            work_params = [f"works[]={work}" for work in request.works]

        author_params = []
        if hasattr(request, 'authors') and request.authors:
            author_params = [f"authors[]={author}" for author in request.authors]

        # Build the final URL with array parameters
        base_params = urlencode(params)
        array_params = "&".join(work_params + author_params)

        if array_params:
            final_url = f"{MANTICORE_API_URL}?{base_params}&{array_params}"
        else:
            final_url = f"{MANTICORE_API_URL}?{base_params}"

        logger.debug(f"Making request to Manticore API: {final_url}")
        response = requests.get(final_url, timeout=10)
        logger.debug(f"Manticore API response status: {response.status_code}")

        # Check for HTTP errors
        response.raise_for_status()

        # Log response for debugging (truncated)
        response_preview = response.text[:200] + "..." if len(response.text) > 200 else response.text
        logger.debug(f"Manticore API response preview: {response_preview}")

    except requests.exceptions.Timeout:
        logger.error("Timeout occurred while querying Manticore API")
        return {
            "answer": "Search service request timed out. Please try again.",
        }
    except requests.exceptions.ConnectionError:
        logger.error("Connection error occurred while querying Manticore API")
        return {
            "answer": "Unable to connect to search service. Please try again later.",
        }
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        return {
            "answer": f"Search service returned an error: {e}",
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error occurred: {e}")
        return {
            "answer": f"Error occurred while searching: {str(e)}",
        }

    try:
        response_data = clean_manticore_response(response.text)
        logger.debug(f"Successfully parsed {len(response_data)} items from Manticore response")

        paragraphs = [
            {
                "id": item.get('docid', ''),
                "text": item.get('text', ''),
                "record_id": item.get('record_id', ''),
                "author": item.get('authorid', ''),
                "title": item.get('workid', '')
            }
            for item in response_data
            if item.get('text')  # Only include items with actual text content
        ]

        logger.info(f"Retrieved {len(paragraphs)} valid paragraphs for query: {request.query}")
        return paragraphs

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse Manticore response: {e}")
        return {
            "answer": "Error parsing search results. Please try again.",
        }
    except Exception as e:
        logger.error(f"Unexpected error processing Manticore response: {e}")
        return {
            "answer": f"Unexpected error occurred while processing search results: {str(e)}",
        }