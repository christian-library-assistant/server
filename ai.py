import anthropic
import json
import logging
from typing import List, Tuple
from fastapi import HTTPException
import re

from manticore import clean_manticore_response

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class AIClient:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def generate_response(self, system_prompt: str, user_prompt: str, conversation_history: List[dict] = None) -> anthropic.types.Message:
        """
        Generate a response using the Claude API
        """
        messages = []
        
        # Add conversation history if available
        if conversation_history:
            logger.debug(f"Processing conversation history with {len(conversation_history)} messages")
            for msg in conversation_history:
                if msg["role"] == "user":
                    # Store just the query for user messages, not the full prompt with context
                    user_content = msg["content"]
                    # If the content contains CONTEXT: or QUESTION:, extract just the question
                    if "CONTEXT:" in user_content and "QUESTION:" in user_content:
                        user_content = user_content.split("QUESTION:")[-1].strip()
                    
                    messages.append({"role": "user", "content": user_content})
                    logger.debug(f"Added user message: {user_content[:50]}...")
                else:
                    # Keep assistant messages as they are
                    messages.append(msg)
                    logger.debug(f"Added assistant message: {msg['content'][:50]}...")
        
        # Add the current user prompt
        messages.append({"role": "user", "content": user_prompt})
        logger.debug(f"Added current user prompt (length: {len(user_prompt)})")
        
        # Call Claude API to generate response
        logger.debug(f"Calling Claude API with {len(messages)} messages")
        response = self.client.messages.create(
            model="claude-3-7-sonnet-latest",  
            max_tokens=4000,
            temperature=0.1,
            system=system_prompt,
            messages=messages
        )
        
        logger.debug(f"Claude response received (length: {len(response.content[0].text)})")
        return response

def generate_ccel_url(source_id):
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

def clean_ai_response(response: str) -> Tuple[str, List[dict], List[Tuple[str, str]]]:
    """
    Clean and parse the AI response from JSON format.
    If JSON parsing fails, extract useful information from the raw text.
    Also generates CCEL URLs for sources when available.
    
    Args:
        response: Raw response string from Claude
        
    Returns:
        Tuple containing answer text, list of sources, and list of source links
    """
    try:
        logger.debug(f"Cleaning AI response (length: {len(response)})")
        
        # Write response to a temp file for debugging
        with open("cleaned_answer.txt", "w") as f:
            f.write("=============== RAW CLAUDE RESPONSE ===============\n")
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
            
            with open("cleaned_answer.txt", "a") as f:
                f.write("\n\nPrecise JSON match:\n")
                f.write(cleaned_answer)
            
            try:
                response_json = json.loads(cleaned_answer)
                answer_text = response_json.get("answer", "")
                sources = response_json.get("sources", [])
                
                # Generate URLs for sources if needed
                source_urls = []
                for source_id in sources:
                    url = generate_ccel_url(source_id)
                    if url:
                        source_urls.append((source_id, url))
                
                if source_urls:
                    with open("cleaned_answer.txt", "a") as f:
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
                    
                    with open("cleaned_answer.txt", "a") as f:
                        f.write("\n\nGeneral JSON match:\n")
                        f.write(cleaned_answer)
                    
                    response_json = json.loads(cleaned_answer)
                    
                    # Only use this if it has the right fields
                    if "answer" in response_json:
                        answer_text = response_json.get("answer", "")
                        sources = response_json.get("sources", [])

                        # Generate URLs for sources if needed
                        source_urls = []
                        for source_id in sources:
                            url = generate_ccel_url(source_id)
                            if url:
                                source_urls.append((source_id, url))
                        
                        if source_urls:
                            with open("cleaned_answer.txt", "a") as f:
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

def format_user_prompt(paragraphs: List[dict], query: str, is_continuation: bool = False) -> str:
    """
    Format the prompt for the user query with context.
    
    Args:
        paragraphs: List of paragraph objects containing context
        query: User's query text
        is_continuation: Whether this is a follow-up question
        
    Returns:
        Formatted prompt string
    """
    follow_up = ""
    if is_continuation:
        follow_up = "This is a follow-up question in an ongoing conversation. Please consider the conversation history when answering. The user might refer to previous messages or expect you to remember personal details they shared before."
    
    # Log context size
    logger.debug(f"Formatting user prompt with {len(paragraphs)} paragraphs of context")
    
    PROMPT_DIR = "PROMPTS"
    PROMPT = open(f"{PROMPT_DIR}/PROMPT", "r").read()
    
    formatted_prompt = PROMPT.format(paragraphs=paragraphs, query=query, follow_up=follow_up)
    logger.debug(f"User prompt formatted (length: {len(formatted_prompt)})")
    
    return formatted_prompt

def get_theological_system_prompt() -> str:
    """
    Get the default system prompt for theological questions.
    
    Returns:
        System prompt string
    """
    return """You are a theological chatbot that answers questions based on provided context. Your task is to give helpful theological responses while following these critical rules:

RESPONSE FORMAT RULES (HIGHEST PRIORITY):
1. ALWAYS respond with ONLY a valid JSON object in this exact format:
   {"answer": "your text here", "sources": []}
2. NEVER include ANY text before or after the JSON object
3. NEVER include explanation about the JSON format
4. NEVER use markdown formatting
5. NEVER place the JSON inside code blocks
6. Make sure the JSON is properly formatted with quotes around keys and string values
7. Your entire response must be parseable as JSON - test it mentally before responding
8. This JSON format is MANDATORY for EVERY response

CITATION RULES:
1. For each source you reference, include a proper citation in your answer text
2. Format citations as: (Author, Work Title)
3. Include the source's record_id in the sources array
4. Be accurate and complete in your citations

CONTENT RULES:
1. Be conversational and natural
2. Acknowledge and build upon previous conversation turns
3. NEVER mention "context", "paragraphs provided", "information available", or similar phrases
4. NEVER say "based on the information provided" or "in the materials available"
5. NEVER mention "I don't see information about X in the context/paragraphs"
6. If you lack information, simply say "I don't have enough information about [topic]" without mentioning context
7. Always phrase as if knowledge comes from your own understanding
8. The user must NEVER know you're working with provided context
9. Include direct quotes when appropriate, but don't mention "from the provided context"

If you follow these rules correctly, especially the JSON format and citation requirements, you will be providing an excellent service."""
