# Copyright 2025 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
from typing import List, Tuple, Dict, Any, Optional
import re

from google import genai
from google.genai import types
from prompts import get_system_prompt, get_user_prompt, get_continuation_text

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class GeminiAIClient:
    """Client for interacting with Google's Gemini AI models."""
    
    def __init__(self, api_key: str, model_id: str = "gemini-2.5-flash-preview-04-17"):
        """
        Initialize the Gemini AI client.
        
        Args:
            api_key: API key for authentication
            model_id: Gemini model ID to use
        """
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id
    
    def generate_response(self, system_prompt: str, user_prompt: str, 
                         conversation_history: Optional[List[dict]] = None,
                         thinking_budget: int = 5000) -> Dict[str, Any]:
        """
        Generate a response using Gemini models with thinking capabilities.
        
        Args:
            system_prompt: System prompt to guide the model
            user_prompt: User's prompt/query
            conversation_history: Previous conversation history
            thinking_budget: Maximum tokens for thinking (Gemini 2.5 Flash only)
            
        Returns:
            Response object with text and metadata
        """
        # Format messages for Gemini - each message needs a role and parts
        formatted_messages = []
        
        # Add conversation history if available
        if conversation_history:
            logger.debug(f"Processing conversation history with {len(conversation_history)} messages")
            
            # Construct conversation history for Gemini
            for msg in conversation_history:
                if msg["role"] == "user":
                    # Extract just the query for user messages
                    user_content = msg["content"]
                    # If the content contains CONTEXT: or QUESTION:, extract just the question
                    if "CONTEXT:" in user_content and "QUESTION:" in user_content:
                        user_content = user_content.split("QUESTION:")[-1].strip()
                    
                    # Add as user message
                    formatted_messages.append({
                        "role": "user", 
                        "parts": [{"text": user_content}]
                    })
                    logger.debug(f"Added user message: {user_content[:50]}...")
                elif msg["role"] == "assistant":
                    # Keep assistant messages as they are
                    formatted_messages.append({
                        "role": "model", 
                        "parts": [{"text": msg["content"]}]
                    })
                    logger.debug(f"Added assistant message: {msg['content'][:50]}...")
        
        # Prepare the full prompt with system instructions and user query
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # Add the current user prompt
        if formatted_messages:
            # If we have history, add as a new message
            formatted_messages.append({
                "role": "user", 
                "parts": [{"text": combined_prompt}]
            })
        else:
            # If no history, start fresh with the combined prompt
            formatted_messages = [{
                "role": "user", 
                "parts": [{"text": combined_prompt}]
            }]
        
        logger.debug(f"Calling Gemini with {len(formatted_messages)} messages")
        
        try:
            
            # Call Gemini API to generate response
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=formatted_messages,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=thinking_budget
                    ),
                    
                ),
                
            )
            print("Prompt tokens:",response.usage_metadata.prompt_token_count)
            print("Thoughts tokens:",response.usage_metadata.thoughts_token_count)
            print("Output tokens:",response.usage_metadata.candidates_token_count)
            print("Total tokens:",response.usage_metadata.total_token_count)
            #send the response to a temp file for debugging
            with open("gemini_response.txt", "w") as f:
                f.write(str(response))
                f.write("\n\n=============== END RAW RESPONSE ===============\n\n")
            
            logger.debug(f"Gemini response received (length: {len(response.text)})")
            
            # Create a response object similar to Claude's
            result = {
                "content": [{"text": response.text}],
                "metadata": {}
            }
            
            # Add metadata if available
            if hasattr(response, 'usage_metadata'):
                result["metadata"] = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "thinking_tokens": response.usage_metadata.thoughts_token_count if hasattr(response.usage_metadata, 'thoughts_token_count') else 0,
                    "output_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count
                }
                logger.debug(f"Thinking tokens: {result['metadata'].get('thinking_tokens', 0)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            # Return empty response in case of error
            return {"content": [{"text": f"Error generating response from Gemini: {str(e)}"}]}

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

def clean_ai_response(response: str) -> Tuple[str, List[dict], Dict[str, str]]:
    """
    Clean and parse the AI response from JSON format.
    If JSON parsing fails, extract useful information from the raw text.
    Also generates CCEL URLs for sources when available.
    
    Args:
        response: Raw response string from Gemini
        
    Returns:
        Tuple containing answer text, list of sources (with citation and record_id), and dictionary of source links
    """
    try:
        logger.debug(f"Cleaning AI response (length: {len(response)})")
        
        # Write response to a temp file for debugging
        with open("cleaned_answer.txt", "w") as f:
            f.write("=============== RAW GEMINI RESPONSE ===============\n")
            f.write(response)
            f.write("\n\n=============== END RAW RESPONSE ===============\n\n")
            
            # Add additional details about the response
            f.write("Response starts with: " + response[:50].replace('\n', ' ') + "...\n")
            f.write("Response ends with: ..." + response[-50:].replace('\n', ' ') + "\n")
            f.write("Response length: " + str(len(response)) + " characters\n")
            f.write("Contains JSON-like braces: " + str("{" in response and "}" in response) + "\n\n")
        
        # First, check for Markdown code blocks containing JSON
        code_block_pattern = r'```(?:json)?\n(.*?)\n```'
        code_blocks = re.findall(code_block_pattern, response, re.DOTALL)
        
        if code_blocks:
            logger.debug("Found markdown code block that might contain JSON")
            for block in code_blocks:
                try:
                    # Try to parse the code block as JSON
                    json_data = json.loads(block)
                    
                    # Check if this JSON has the expected structure
                    if "answer" in json_data and "sources" in json_data:
                        logger.debug("Successfully parsed JSON from markdown code block")
                        
                        answer_text = json_data.get("answer", "")
                        sources = json_data.get("sources", [])
                        
                        # Generate URLs for sources
                        source_links = {}
                        for source in sources:
                            if isinstance(source, dict) and "record_id" in source:
                                record_id = source.get("record_id", "")
                                url = generate_ccel_url(record_id)
                                if url:
                                    source_links[record_id] = url
                        
                        logger.debug(f"Parsed JSON in code block: answer length={len(answer_text)}, sources={len(sources)}")
                        return answer_text, sources, source_links
                except json.JSONDecodeError:
                    # Not valid JSON, try the next block or continue with other strategies
                    pass
        
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
                
                # Check if answer_text itself is a JSON string and try to parse it
                if answer_text and answer_text.startswith("{") and answer_text.endswith("}"):
                    try:
                        # Try to parse answer as JSON
                        nested_json = json.loads(answer_text)
                        if isinstance(nested_json, dict) and "answer" in nested_json and "sources" in nested_json:
                            logger.debug("Found nested JSON in answer field, extracting contents")
                            # Use the nested answer
                            answer_text = nested_json.get("answer", "")
                            # Add sources from nested JSON
                            nested_sources = nested_json.get("sources", [])
                            if nested_sources:
                                sources = nested_sources
                    except json.JSONDecodeError:
                        # If it's not valid JSON, keep it as is
                        logger.debug("Answer looks like JSON but couldn't parse it, keeping as is")
                
                # Generate URLs for sources
                source_links = {}
                for source in sources:
                    if isinstance(source, dict) and "record_id" in source:
                        record_id = source.get("record_id", "")
                        url = generate_ccel_url(record_id)
                        if url:
                            source_links[record_id] = url
                
                if source_links:
                    with open("cleaned_answer.txt", "a") as f:
                        f.write("\n\nGenerated URLs for sources:\n")
                        for source_id, url in source_links.items():
                            f.write(f"{source_id} -> {url}\n")
                
                logger.debug(f"Precise JSON parsing successful: answer length={len(answer_text)}, sources={len(sources)}")
                return answer_text, sources, source_links
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
                        
                        # Check if answer_text itself is a JSON string and try to parse it
                        if answer_text and answer_text.startswith("{") and answer_text.endswith("}"):
                            try:
                                # Try to parse answer as JSON
                                nested_json = json.loads(answer_text)
                                if isinstance(nested_json, dict) and "answer" in nested_json and "sources" in nested_json:
                                    logger.debug("Found nested JSON in answer field, extracting contents")
                                    # Use the nested answer
                                    answer_text = nested_json.get("answer", "")
                                    # Add sources from nested JSON
                                    nested_sources = nested_json.get("sources", [])
                                    if nested_sources:
                                        sources = nested_sources
                            except json.JSONDecodeError:
                                # If it's not valid JSON, keep it as is
                                logger.debug("Answer looks like JSON but couldn't parse it, keeping as is")
                        
                        # Generate URLs for sources
                        source_links = {}
                        for source in sources:
                            if isinstance(source, dict) and "record_id" in source:
                                record_id = source.get("record_id", "")
                                url = generate_ccel_url(record_id)
                                if url:
                                    source_links[record_id] = url
                        
                        if source_links:
                            with open("cleaned_answer.txt", "a") as f:
                                f.write("\n\nGenerated URLs for sources:\n")
                                for source_id, url in source_links.items():
                                    f.write(f"{source_id} -> {url}\n")
                        
                        logger.debug(f"General JSON parsing successful: answer length={len(answer_text)}, sources={len(sources)}")
                        return answer_text, sources, source_links
                except json.JSONDecodeError:
                    continue  # Try the next match
            
            logger.warning("All JSON matches failed to parse properly")
        
        # Strategy 3: If we still don't have valid JSON, try to construct it
        # Look for text that appears to be the answer
        logger.debug("Attempting to construct JSON from raw text")
        
        with open("cleaned_answer.txt", "a") as f:
            f.write("\n\nAttempting to construct JSON from raw text")
        
        # Extract potential citations from the text
        sources = []
        citation_pattern = r'\(([^)]+)\)'
        citation_matches = re.findall(citation_pattern, response)
        for citation in citation_matches:
            # Create a placeholder record_id based on the citation
            if "summa" in citation.lower():
                record_id = "ccel/a/aquinas/summa.xml"
            elif "augustine" in citation.lower():
                record_id = "ccel/a/augustine/city.xml"
            else:
                # Create a generic record_id
                record_id = f"unknown/{citation.lower().replace(' ', '_')}"
            
            sources.append({
                "citation": f"({citation})",
                "record_id": record_id
            })
        
        # Generate URLs for sources
        source_links = {}
        for source in sources:
            record_id = source.get("record_id")
            url = generate_ccel_url(record_id)
            if url:
                source_links[record_id] = url
        
        # Construct a JSON object with the raw response as the answer
        constructed_json = {
            "answer": response,
            "sources": sources,
            "source_links": source_links
        }
        
        with open("cleaned_answer.txt", "a") as f:
            f.write("\n\nConstructed JSON:\n")
            f.write(json.dumps(constructed_json, indent=2))
        
        logger.debug(f"Using raw text as answer: length={len(response)}, sources={len(sources)}")
        return response, sources, source_links

    except Exception as e:
        logger.error(f"Unexpected error in clean_response: {str(e)}")
        # In case of any error, return the raw response to avoid completely failing
        return response, [], {}

def get_theological_system_prompt() -> str:
    """
    Get the default system prompt for theological questions.
    
    Returns:
        System prompt string
    """
    return get_system_prompt()

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
        follow_up = get_continuation_text()
    
    # Log context size
    logger.debug(f"Formatting user prompt with {len(paragraphs)} paragraphs of context")
    
    formatted_prompt = get_user_prompt(paragraphs, query, follow_up)
    logger.debug(f"User prompt formatted (length: {len(formatted_prompt)})")
    
    return formatted_prompt 