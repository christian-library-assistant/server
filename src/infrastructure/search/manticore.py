import json
import requests
import logging
from typing import List, Dict, Any, Union

from ...config.settings import MANTICORE_API_URL
from ...models.schemas import UserQuery

logger = logging.getLogger(__name__)


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
        request: UserQuery containing the search query

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

        logger.debug(f"Making request to Manticore API for query: {request.query}")
        response = requests.get(
            MANTICORE_API_URL,
            params={"text": request.query},
            timeout=10
        )
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