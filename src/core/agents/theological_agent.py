"""
Theological Agent using LangChain's ReAct framework with Claude models.

This agent can reason about theological questions and decide when to search
the CCEL database for relevant information.
"""

import logging
from tabnanny import verbose
from typing import List, Dict, Any, Optional, Union

from langchain_anthropic import ChatAnthropic
from langchain.agents import create_react_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from pydantic import SecretStr

from ..tools.manticore_tool import search_ccel_database, get_ccel_source_details
from ..tools.author_works_tools import search_ccel_authors, search_ccel_works
from ...config.settings import ANTHROPIC_API_KEY
from ...prompts.agent_prompts import THEOLOGICAL_AGENT_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class TheologicalAgent:
    """
    An intelligent theological agent that can search Christian texts and
    provide reasoned responses to theological questions.
    """

    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022", temperature: float = 0.1):
        """
        Initialize the theological agent.

        Args:
            model_name: Claude model to use
            temperature: Temperature for response generation
        """
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required for TheologicalAgent")

        self.model_name = model_name
        self.temperature = temperature

        # Initialize the LLM
        self.llm = ChatAnthropic(
            model_name=model_name,
            timeout=10,
            stop=["\n\nHuman:", "\n\nAssistant:"],
            verbose=True,
            temperature=temperature,
            api_key=SecretStr(ANTHROPIC_API_KEY)
        )

        # Define available tools #TODO: Add the bible verse tool and the web_search_tool.
        self.tools = [
            search_ccel_database,
            search_ccel_authors,
            search_ccel_works,
            get_ccel_source_details
        ]

        # Create custom prompt for theological reasoning
        self.prompt_template = self._create_prompt_template()

        # Create the agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt_template
        )

        # Create agent executor with memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            memory=self.memory,
            max_iterations=5,
            early_stopping_method="force",
            handle_parsing_errors=True
        )

        logger.info(f"Initialized TheologicalAgent with model: {model_name}")

    def _create_prompt_template(self) -> PromptTemplate:
        """Create a custom prompt template optimized for theological reasoning."""
        return PromptTemplate(
            template=THEOLOGICAL_AGENT_PROMPT_TEMPLATE,
            input_variables=["input", "chat_history", "agent_scratchpad"],
            partial_variables={"tools": self._format_tools(), "tool_names": self._get_tool_names()}
        )

    def _format_tools(self) -> str:
        """Format tools for the prompt."""
        tool_strings = []
        for tool in self.tools:
            tool_strings.append(f"- {tool.name}: {tool.description}")
        return "\n".join(tool_strings)

    def _get_tool_names(self) -> str:
        """Get comma-separated tool names."""
        return ", ".join([tool.name for tool in self.tools])

    def _build_filter_context(self, authors: Optional[List[str]] = None, works: Optional[List[str]] = None) -> str:
        """
        Build filter context string for the prompt.

        Args:
            authors: Optional list of author IDs to filter by
            works: Optional list of work IDs to filter by

        Returns:
            Formatted filter context string
        """
        if not authors and not works:
            return ""

        context_parts = []
        context_parts.append("🔍 SEARCH FILTERS APPLIED:")
        context_parts.append("The user has requested that ALL searches be limited to the following:")

        if authors:
            authors_str = ", ".join(f'"{a}"' for a in authors)
            context_parts.append(f"  • Authors: {authors_str}")

        if works:
            works_str = ", ".join(f'"{w}"' for w in works)
            context_parts.append(f"  • Works: {works_str}")

        context_parts.append("")
        context_parts.append("IMPORTANT: When you use search_ccel_database, you MUST pass these filte   r values:")
        if authors:
            context_parts.append(f'  authors="{",".join(authors)}"')
        if works:
            context_parts.append(f'  works="{",".join(works)}"')
        context_parts.append("")
        context_parts.append("This ensures all search results come only from the specified authors/works.")
        context_parts.append("=" * 80)

        return "\n".join(context_parts)

    def query(self, question: str, authors: Optional[List[str]] = None, works: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Process a theological question and return a structured response.

        Args:
            question: The theological question or query
            authors: Optional list of author IDs to filter search results
            works: Optional list of work IDs to filter search results

        Returns:
            Dictionary containing the response and sources
        """
        try:
            logger.debug(f"Processing theological query: {question}")

            # Build filter context for the prompt
            filter_context = self._build_filter_context(authors, works)

            # Prepend filter context to the question if filters are provided
            if filter_context:
                full_input = f"{filter_context}\n\nUser Question: {question}"
            else:
                full_input = question

            # Execute the agent with the full input
            response = self.agent_executor.invoke({"input": full_input})

            # Extract the final answer
            answer = response.get("output", "I apologize, but I encountered an error processing your question.")

            # Extract sources from tool usage in agent iterations
            sources = self._extract_sources_from_tool_usage(response.get("intermediate_steps", []), answer)

            logger.info(f"Successfully processed theological query with {len(sources)} sources")

            return {
                "answer": answer,
                "sources": sources,
                "metadata": {
                    "model": self.model_name,
                    "agent_iterations": response.get("intermediate_steps", [])
                }
            }

        except Exception as e:
            logger.error(f"Error processing theological query: {str(e)}")
            return {
                "answer": f"I apologize, but I encountered an error while processing your question: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e)}
            }


    def _extract_sources_from_tool_usage(self, intermediate_steps: List, answer: str) -> List[Dict[str, str]]:
        """
        Extract sources from actual tool usage in agent iterations.
        Returns record IDs only - links will be generated later by SourceFormatter.
        """
        sources = []

        for step in intermediate_steps:
            if len(step) >= 2:  # (action, observation)
                action, observation = step

                # Check if this was a search_ccel_database action
                if hasattr(action, 'tool') and action.tool == 'search_ccel_database':
                    try:
                        # observation should contain the search results
                        content = str(observation)

                        # Extract source info from search results
                        # This would need to match the format returned by search_ccel_database
                        import re

                        # Look for record_id patterns in the tool output
                        record_id_matches = re.findall(r'record_id[\'"]?\s*:\s*[\'"]?(\w+)[\'"]?', content)

                        for record_id in record_id_matches:
                            if record_id:
                                sources.append({
                                    "citation": f"CCEL Record {record_id}",
                                    "record_id": record_id
                                    # Note: No link generation here - SourceFormatter will handle this
                                })
                    except Exception as e:
                        logger.error(f"Error extracting sources from tool usage: {e}")

        # If no sources from tool usage, fall back to text extraction
        if not sources:
            return self._extract_sources_from_answer_text(answer)

        return sources

    def _extract_sources_from_answer_text(self, answer: str) -> List[Dict[str, str]]:
        """
        Extract source citations from the answer text.
        First tries to parse the SOURCES section, then falls back to citation patterns.
        """
        import re
        import json
        sources = []

        # First, try to extract the SOURCES section from the agent's answer
        sources_pattern = r'SOURCES:\s*(\[.*?\])'
        sources_match = re.search(sources_pattern, answer, re.DOTALL)

        if sources_match:
            try:
                sources_text = sources_match.group(1)
                # Fix common JSON issues that might occur
                sources_text = sources_text.replace("'", '"')
                sources_data = json.loads(sources_text)

                for source in sources_data:
                    if isinstance(source, dict):
                        sources.append({
                            "record_id": source.get("record_id", ""),
                            "citation": source.get("citation", ""),
                            "link": source.get("link", "")
                        })

                logger.debug(f"Extracted {len(sources)} sources from SOURCES section")
                return sources

            except (json.JSONDecodeError, Exception) as e:
                logger.debug(f"Failed to parse SOURCES section: {e}")

        # Fallback to pattern matching for inline citations
        citation_pattern = r'\(([^,]+),\s*([^)]+)\)'
        matches = re.findall(citation_pattern, answer)

        for match in matches:
            author, work = match
            sources.append({
                "citation": f"{author.strip()}, {work.strip()}",
                "record_id": "",  # Would need to be extracted from tool usage
                "link": f"https://www.ccel.org/search?q={author.strip().replace(' ', '+')}"
            })

        logger.debug(f"Extracted {len(sources)} sources from citation patterns")
        return sources

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history from memory."""
        history = []
        try:
            messages = self.memory.chat_memory.messages
            for message in messages:
                if isinstance(message, HumanMessage):
                    history.append({"role": "user", "content": message.content})
                elif isinstance(message, AIMessage):
                    history.append({"role": "assistant", "content": message.content})

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")

        return history

    def reset_conversation(self):
        """Reset the conversation memory."""
        self.memory.clear()
        logger.debug("Conversation memory cleared")