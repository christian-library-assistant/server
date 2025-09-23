import json
import logging
import re
from typing import List, Tuple, Dict, Any
from ...config.settings import IS_DEVELOPMENT

logger = logging.getLogger(__name__)
# Only set debug level in development
if IS_DEVELOPMENT:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)


def generate_ccel_url(source_id: str) -> str | None:
    """
    Generate a CCEL URL from a source ID.

    Args:
        source_id: Source ID in the format "ccel/a/author/work.xml:section-p#"

    Returns:
        URL in the format "https://ccel.org/ccel/author/work/work.section.html"
    """
    try:
        # Only process CCEL sources
        if not source_id.startswith("ccel/"):
            return None

        # Split on colon to separate path from section
        parts = source_id.split(":")
        path_part = parts[0]  # ccel/a/anonymous/westminster3.xml

        # Split the path to extract components
        path_components = path_part.split("/")

        # We need at least 3 components: ccel, a, anonymous/work
        if len(path_components) >= 3:
            # Ignore the 'a' part (or whatever comes after ccel/)
            author = path_components[2]  # anonymous

            # Get work name, removing .xml if present
            work = path_components[3] if len(path_components) > 3 else ""
            work = work.split(".")[0]  # remove .xml

            # Get section part (before any "-" if present)
            section = ""
            if len(parts) > 1:
                section = parts[1].split("-")[0]  # i.xxi

            # Construct URL following the pattern
            url = f"https://ccel.org/ccel/{author}/{work}/{work}.{section}.html"
            return url
    except Exception as e:
        logger.error(f"Error generating URL for {source_id}: {str(e)}")

    return None


def clean_ai_response(response: str) -> Tuple[str, List[Dict[str, Any]], List[Tuple[str, str]]]:
    """
    Clean and parse the AI response from JSON format.
    If JSON parsing fails, extract useful information from the raw text.
    Also generates CCEL URLs for sources when available.

    Args:
        response: Raw response string from AI model

    Returns:
        Tuple containing answer text, list of sources, and list of source links
    """
    try:
        logger.debug(f"Cleaning AI response (length: {len(response)})")

        # Write response to a temp file for debugging
        with open("data/cleaned_answer.txt", "w") as f:
            f.write("=============== RAW AI RESPONSE ===============\n")
            f.write(response)
            f.write("\n\n=============== END RAW RESPONSE ===============\n\n")

            # Add additional details about the response
            f.write("Response starts with: " + response[:50].replace('\n', ' ') + "...\n")
            f.write("Response ends with: ..." + response[-50:].replace('\n', ' ') + "\n")
            f.write("Response length: " + str(len(response)) + " characters\n")
            f.write("Contains JSON-like braces: " + str("{" in response and "}" in response) + "\n\n")

        # Try multiple JSON extraction strategies

        # Strategy 1: First try to extract JSON using a more precise pattern
        # This looks for a JSON object with "answer" and "sources" fields
        precise_json_pattern = r'\{\s*"answer"\s*:\s*"[^"]*(?:"[^"]*)*"\s*,\s*"sources"\s*:\s*\[.*?\]\s*\}'
        precise_matches = re.findall(precise_json_pattern, response, re.DOTALL)

        if precise_matches:
            logger.debug("Found precise JSON match")
            cleaned_answer = precise_matches[0]

            with open("data/cleaned_answer.txt", "a") as f:
                f.write("\n\nPrecise JSON match:\n")
                f.write(cleaned_answer)

            try:
                response_json = json.loads(cleaned_answer)
                answer_text = response_json.get("answer", "")
                sources = response_json.get("sources", [])

                # Generate URLs for sources if needed
                source_urls = []
                for source_data in sources:
                    if isinstance(source_data, dict):
                        source_id = source_data.get("record_id", "")
                    else:
                        source_id = source_data

                    url = generate_ccel_url(source_id)
                    if url:
                        source_urls.append((source_id, url))

                if source_urls:
                    with open("data/cleaned_answer.txt", "a") as f:
                        f.write("\n\nGenerated URLs for sources:\n")
                        for source_id, url in source_urls:
                            f.write(f"{source_id} -> {url}\n")

                logger.debug(f"Precise JSON parsing successful: answer length={len(answer_text)}, sources={len(sources)}")
                return answer_text, sources, source_urls
            except json.JSONDecodeError:
                logger.warning("Precise JSON match failed to parse")
                # Fall through to next strategy

        # Strategy 2: Try to find any JSON-like structure (more permissive)
        json_pattern = r'\{.*?\}'
        json_matches = re.findall(json_pattern, response, re.DOTALL)

        if json_matches:
            # Try parsing as JSON first
            for match in json_matches:
                try:
                    cleaned_answer = match

                    with open("data/cleaned_answer.txt", "a") as f:
                        f.write("\n\nGeneral JSON match:\n")
                        f.write(cleaned_answer)

                    response_json = json.loads(cleaned_answer)

                    # Only use this if it has the right fields
                    if "answer" in response_json:
                        answer_text = response_json.get("answer", "")
                        sources = response_json.get("sources", [])

                        # Generate URLs for sources if needed
                        source_urls = []
                        for source_data in sources:
                            if isinstance(source_data, dict):
                                source_id = source_data.get("record_id", "")
                            else:
                                source_id = source_data

                            url = generate_ccel_url(source_id)
                            if url:
                                source_urls.append((source_id, url))

                        if source_urls:
                            with open("data/cleaned_answer.txt", "a") as f:
                                f.write("\n\nGenerated URLs for sources:\n")
                                for source_id, url in source_urls:
                                    f.write(f"{source_id} -> {url}\n")

                        logger.debug(f"General JSON parsing successful: answer length={len(answer_text)}, sources={len(sources)}")
                        return answer_text, sources, source_urls
                except json.JSONDecodeError:
                    continue  # Try the next match

            logger.warning("All JSON matches failed to parse properly")

        # Strategy 3: If we still don't have valid JSON, try to construct it
        # Look for text that appears to be the answer
        logger.debug("Attempting to construct JSON from raw text")

        with open("cleaned_answer.txt", "a") as f:
            f.write("\n\nAttempting to construct JSON from raw text")

        # Extract sources if they exist
        sources = []
        source_pattern = r'source[s]?:\s*(.*?)(?:\n|\Z)'
        source_matches = re.findall(source_pattern, response, re.IGNORECASE | re.DOTALL)

        if source_matches:
            # Process source text into a list
            source_text = source_matches[0]
            source_candidates = re.split(r'\d+\.|\n|,', source_text)
            sources = [s.strip() for s in source_candidates if s.strip()]

        # Construct a JSON object with the raw response as the answer
        constructed_json = {
            "answer": response,
            "sources": sources
        }

        with open("cleaned_answer.txt", "a") as f:
            f.write("\n\nConstructed JSON:\n")
            f.write(json.dumps(constructed_json, indent=2))

        logger.debug(f"Using raw text as answer: length={len(response)}, sources={len(sources)}")
        return response, sources, []

    except Exception as e:
        logger.error(f"Unexpected error in clean_response: {str(e)}")
        # In case of any error, return the raw response to avoid completely failing
        return response, [], []


def deduplicate_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate sources based on record_id.

    Args:
        sources: List of source dictionaries with record_id, link, and citation_text

    Returns:
        Deduplicated list of sources
    """
    seen_record_ids = set()
    unique_sources = []

    for source in sources:
        record_id = source.get("record_id")
        if record_id and record_id not in seen_record_ids:
            seen_record_ids.add(record_id)
            unique_sources.append(source)

    return unique_sources