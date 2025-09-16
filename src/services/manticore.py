import json
import requests
from typing import List, Dict, Any

from ..config.settings import MANTICORE_API_URL
from ..models.schemas import UserQuery


def clean_manticore_response(response_text: str) -> List[Dict[str, Any]]:
    """
    Clean and parse response from Manticore search service.

    Args:
        response_text: Raw response text from Manticore API

    Returns:
        List of parsed response items
    """
    raw_response = response_text
    json_start = raw_response.find('[')
    json_end = raw_response.rfind(']') + 1
    json_response = raw_response[json_start:json_end]
    return json.loads(json_response)


def get_paragraphs(request: UserQuery) -> List[Dict[str, str]] | Dict[str, str]:
    """
    Get paragraphs from Manticore API for a given query.

    Args:
        request: UserQuery containing the search query

    Returns:
        List of paragraph dictionaries containing text and metadata
    """
    try:
        response = requests.get(MANTICORE_API_URL, params={"text": request.query}, timeout=5)
        print(response.text)
    except requests.exceptions.ReadTimeout as e:
        return {
            "answer": f"Musa's endpoint is dead, {e.__class__.__name__}",
        }

    response_data = clean_manticore_response(response.text)
    paragraphs = [
        {
            "id": item.get('docid'),
            "text": item['text'],
            "record_id": item.get('record_id', ''),
            "author": item.get('authorid', ''),
            "title": item.get('workid', '')
        }
        for item in response_data
    ]
    return paragraphs