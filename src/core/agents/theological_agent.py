"""
Theological Agent using LangChain's ReAct framework with Claude models.

This agent can reason about theological questions and decide when to search
the CCEL database for relevant information.
"""

import logging
from tabnanny import verbose
from typing import List, Dict, Any, Optional

from langchain_anthropic import ChatAnthropic
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import StructuredTool
from pydantic import SecretStr

from ..tools.manticore_tool import (
    search_ccel_database,
    get_ccel_source_details,
    _search_ccel_database_impl,
    SearchCCELInput,
)
from ..tools.author_works_tools import search_ccel_authors, search_ccel_works
from ...config.settings import ANTHROPIC_API_KEY
from ...prompts.agent_prompts import THEOLOGICAL_AGENT_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class TheologicalAgent:
    """
    An intelligent theological agent that can search Christian texts and
    provide reasoned responses to theological questions.
    """

    def __init__(self, model_name: str = "claude-haiku-4-5", temperature: float = 0.1):
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

        # Store current filters as instance variables (not in conversation memory)
        self.current_authors: Optional[List[str]] = None
        self.current_works: Optional[List[str]] = None

        # Initialize the LLM
        self.llm = ChatAnthropic(
            model_name=model_name,
            max_tokens=8192,  # Increased from default 1024 to allow comprehensive theological responses
            timeout=30,  # Increased from 10 to 30 seconds to accommodate longer generation
            stop=None,  # Let ReAct parser handle termination via format keywords
            verbose=True,
            temperature=temperature,
            api_key=SecretStr(ANTHROPIC_API_KEY),
        )

        # Define base tools (non-search tools that don't need filter injection)
        self.base_tools = [
            search_ccel_authors,
            search_ccel_works,
            get_ccel_source_details,
        ]

        # Create custom prompt for theological reasoning
        self.prompt_template = self._create_prompt_template()

        # Create agent executor with memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )

        # Build the agent with initial (empty) filters
        self._rebuild_agent()

        logger.info(f"Initialized TheologicalAgent with model: {model_name}")

    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create a custom prompt template optimized for theological reasoning."""
        return ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

    def _build_system_prompt_with_filters(self) -> str:
        """
        Build the system prompt with current filter context appended.

        This keeps the agent aware of active filters without storing them in conversation memory.
        The filter context is injected into the system prompt on every query.

        Returns:
            Complete system prompt with filter context if filters are active
        """
        base_prompt = THEOLOGICAL_AGENT_PROMPT_TEMPLATE

        if not self.current_authors and not self.current_works:
            return base_prompt

        # Build concise filter context for system awareness
        filter_parts = []
        if self.current_authors:
            authors_str = ", ".join(self.current_authors)
            filter_parts.append(f"Authors: {authors_str}")
        if self.current_works:
            works_str = ", ".join(self.current_works)
            filter_parts.append(f"Works: {works_str}")

        filter_context = "\n\n" + "=" * 80 + "\n"
        filter_context += "🔍 ACTIVE SEARCH FILTERS\n"
        filter_context += (
            "The user has applied the following filters to limit search results:\n"
        )
        filter_context += "  • " + "\n  • ".join(filter_parts) + "\n"
        filter_context += "\nWhen the user asks about 'this author' or 'this work', they are referring to the filtered items above.\n"
        filter_context += (
            "All searches will automatically be limited to these filters.\n"
        )
        filter_context += "=" * 80

        return base_prompt + filter_context

    def _create_filter_injecting_search_tool(self):
        """
        Create a wrapper around search_ccel_database that automatically injects
        current filter values when the tool is called.

        This keeps filters separate from conversation memory while still ensuring
        they're applied to searches.
        """

        def search_with_filters(
            query: str, authors: str = "", works: str = "", top_k: int = 20
        ) -> str:
            # Override with current filters if they exist
            effective_authors = (
                ",".join(self.current_authors) if self.current_authors else authors
            )
            effective_works = (
                ",".join(self.current_works) if self.current_works else works
            )

            if self.current_authors or self.current_works:
                logger.info(
                    f"Injecting filters into search: authors={effective_authors}, works={effective_works}"
                )

            # Call the original implementation with injected filters
            return _search_ccel_database_impl(
                query, effective_authors, effective_works, top_k
            )

        # Create the tool with the same interface as the original
        return StructuredTool.from_function(
            func=search_with_filters,
            name="search_ccel_database",
            description=search_ccel_database.description,
            args_schema=SearchCCELInput,
            return_direct=False,
        )

    def _rebuild_agent(self):
        """
        Rebuild the agent and executor with current filter settings.
        This is called when filters change to inject them into the search tool
        and update the system prompt with filter context.
        """
        # Create filter-injecting search tool
        search_tool = self._create_filter_injecting_search_tool()

        # Combine with base tools
        self.tools = [search_tool] + self.base_tools

        # Build system prompt with current filter context
        system_prompt_with_filters = self._build_system_prompt_with_filters()

        # Create updated prompt template with current filters
        current_prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt_with_filters),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # Create the agent with updated tools and prompt
        self.agent = create_tool_calling_agent(
            llm=self.llm, tools=self.tools, prompt=current_prompt_template
        )

        # Create agent executor (reuses existing memory)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            memory=self.memory,
            max_iterations=15,
            max_execution_time=120,
            early_stopping_method="force",
            handle_parsing_errors="Check your output format. You MUST include 'Final Answer:' in EVERY response, even for simple greetings. Follow the pattern: Thought: [reasoning]\nFinal Answer: [response]",
            return_intermediate_steps=True,
        )

    def _extract_text_from_content(self, content: Any) -> str:
        """
        Extract text from message content, handling both string and list formats.

        Tool-calling agents return content as list of content blocks:
        [{'text': '...', 'type': 'text', 'index': 0}]

        ReAct agents return simple strings.

        Args:
            content: Message content (string, list of content blocks, or other)

        Returns:
            Extracted text as string
        """
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Extract text from all text blocks
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    # Handle simple string items in list
                    text_parts.append(block)
            return " ".join(text_parts)
        else:
            logger.warning(f"Unexpected content type: {type(content)}")
            return str(content)

    def query(
        self,
        question: str,
        authors: Optional[List[str]] = None,
        works: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
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
            logger.debug(f"Filters - Authors: {authors}, Works: {works}")

            # Update current filters if they've changed
            filters_changed = (
                self.current_authors != authors or self.current_works != works
            )

            if filters_changed:
                self.current_authors = authors
                self.current_works = works
                logger.info(f"Updated filters: authors={authors}, works={works}")

            # Rebuild agent to include current filter context in system prompt
            # This ensures agent is aware of active filters without storing them in conversation memory
            # We rebuild on every query (not just when filters change) to ensure consistency
            self._rebuild_agent()

            # Execute the agent with the pure question
            # Filter context is already baked into the agent's prompt template (via _rebuild_agent)
            # This gives agent awareness without polluting conversation history
            # Filters will also be automatically injected when the search tool is called
            response = self.agent_executor.invoke({"input": question})

            # Extract the final answer (handle both string and list formats)
            raw_answer = response.get(
                "output",
                "I apologize, but I encountered an error processing your question.",
            )
            answer = self._extract_text_from_content(raw_answer)

            # Extract sources from tool usage in agent iterations and clean the answer
            sources, cleaned_answer = self._extract_sources_from_tool_usage(
                response.get("intermediate_steps", []), answer
            )

            logger.info(
                f"Successfully processed theological query with {len(sources)} sources"
            )

            return {
                "answer": cleaned_answer,
                "sources": sources,
                "metadata": {
                    "model": self.model_name,
                    "agent_iterations": response.get("intermediate_steps", []),
                },
            }

        except Exception as e:
            logger.error(f"Error processing theological query: {str(e)}")
            return {
                "answer": f"I apologize, but I encountered an error while processing your question: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e)},
            }

    def _extract_sources_from_tool_usage(
        self, intermediate_steps: List, answer: str
    ) -> tuple[List[Dict[str, str]], str]:
        """
        Extract sources from actual tool usage in agent iterations.
        Returns record IDs only - links will be generated later by SourceFormatter.

        Returns:
            Tuple of (sources list, cleaned answer text without SOURCES section)
        """
        sources = []

        for step in intermediate_steps:
            if len(step) >= 2:  # (action, observation)
                action, observation = step

                # Check if this was a search_ccel_database action
                if hasattr(action, "tool") and action.tool == "search_ccel_database":
                    try:
                        # observation should contain the search results
                        content = str(observation)

                        # Extract source info from search results
                        # This would need to match the format returned by search_ccel_database
                        import re

                        # Look for record_id patterns in the tool output
                        record_id_matches = re.findall(
                            r'record_id[\'"]?\s*:\s*[\'"]?(\w+)[\'"]?', content
                        )

                        for record_id in record_id_matches:
                            if record_id:
                                sources.append(
                                    {
                                        "citation": f"CCEL Record {record_id}",
                                        "record_id": record_id,
                                        # Note: No link generation here - SourceFormatter will handle this
                                    }
                                )
                    except Exception as e:
                        logger.error(f"Error extracting sources from tool usage: {e}")

        # If no sources from tool usage, fall back to text extraction
        if not sources:
            return self._extract_sources_from_answer_text(answer)

        # If we got sources from tool usage, still clean the answer text
        sources_from_text, cleaned_answer = self._extract_sources_from_answer_text(
            answer
        )
        return sources, cleaned_answer

    def _validate_and_fix_citation_numbers(self, answer: str, num_sources: int) -> str:
        """
        Intelligently renumber citations to match available sources.

        Strategy: Collect all unique citation numbers used in the text, sort them,
        and create a mapping from old numbers to sequential new numbers (1, 2, 3...).

        Example: If agent uses citations [7, 6, 4, 1] with 4 sources:
        - Sort unique numbers: [1, 4, 6, 7]
        - Create mapping: {1→1, 4→2, 6→3, 7→4}
        - Renumber citations accordingly

        Args:
            answer: The answer text with citations
            num_sources: Number of sources in the SOURCES array

        Returns:
            Answer text with renumbered citations
        """
        if num_sources == 0:
            return answer

        import re

        # Collect all unique citation numbers used in the text
        all_citation_nums = set()

        # Find all citation patterns
        superscript_pattern = r"\[\[(\d+)\]\]\(#source-(\d+)\)"
        markdown_pattern = r"\[([^\]]+)\]\(#source-(\d+)\)"
        bare_pattern = r"#source-(\d+)(?!\d)"

        for match in re.finditer(superscript_pattern, answer):
            all_citation_nums.add(int(match.group(2)))

        for match in re.finditer(markdown_pattern, answer):
            if not re.match(r"\[\d+\]", match.group(1)):
                all_citation_nums.add(int(match.group(2)))

        for match in re.finditer(bare_pattern, answer):
            start = match.start()
            if start == 0 or answer[start - 1] not in ["(", "["]:
                all_citation_nums.add(int(match.group(1)))

        if not all_citation_nums:
            return answer

        # Sort the citation numbers and create a mapping to sequential numbers
        sorted_nums = sorted(all_citation_nums)

        # Create mapping: old_num -> new_num (1, 2, 3, ...)
        citation_mapping = {old_num: idx + 1 for idx, old_num in enumerate(sorted_nums)}

        logger.info(f"Citation renumbering: {citation_mapping}")

        # Check if we need to renumber (i.e., if citations don't match 1-N exactly)
        needs_renumbering = sorted_nums != list(range(1, len(sorted_nums) + 1))

        if not needs_renumbering and len(sorted_nums) == num_sources:
            # Citations are already 1, 2, 3, ..., N - no changes needed
            return answer

        # Check if citation count matches source count
        if len(sorted_nums) != num_sources:
            logger.warning(
                f"Citation count mismatch: Found {len(sorted_nums)} unique citations "
                f"but have {num_sources} sources. Mapping: {citation_mapping}"
            )

        fixed_answer = answer

        # Renumber superscript citations: [[N]](#source-N)
        def renumber_superscript(match):
            display_num = int(match.group(1))
            source_num = int(match.group(2))

            new_num = citation_mapping.get(source_num, source_num)
            return f"[[{new_num}]](#source-{new_num})"

        fixed_answer = re.sub(superscript_pattern, renumber_superscript, fixed_answer)

        # Renumber markdown citations: [text](#source-N)
        def renumber_markdown(match):
            text = match.group(1)
            source_num = int(match.group(2))

            new_num = citation_mapping.get(source_num, source_num)
            return f"[{text}](#source-{new_num})"

        fixed_answer = re.sub(markdown_pattern, renumber_markdown, fixed_answer)

        # Renumber bare anchor references: #source-N
        def renumber_bare(match):
            source_num = int(match.group(1))

            new_num = citation_mapping.get(source_num, source_num)
            return f"#source-{new_num}"

        fixed_answer = re.sub(bare_pattern, renumber_bare, fixed_answer)

        logger.info(
            f"Renumbered citations from {sorted_nums} to {list(range(1, len(sorted_nums) + 1))}"
        )

        return fixed_answer

    def _extract_sources_from_answer_text(
        self, answer: str
    ) -> tuple[List[Dict[str, str]], str]:
        """
        Extract source citations from the answer text and remove the SOURCES section.
        First tries to parse the SOURCES section, then falls back to citation patterns.

        Returns:
            Tuple of (sources list, cleaned answer text without SOURCES section)
        """
        import re
        import json

        sources = []
        cleaned_answer = answer

        # First, try to extract the SOURCES section from the agent's answer
        sources_pattern = r"SOURCES:\s*(\[.*?\])"
        sources_match = re.search(sources_pattern, answer, re.DOTALL)

        if sources_match:
            try:
                sources_text = sources_match.group(1)
                # Fix common JSON issues that might occur
                sources_text = sources_text.replace("'", '"')
                sources_data = json.loads(sources_text)

                for source in sources_data:
                    if isinstance(source, dict):
                        sources.append(
                            {
                                "record_id": source.get("record_id", ""),
                                "citation": source.get("citation", ""),
                                "link": source.get("link", ""),
                            }
                        )

                # Remove the SOURCES section from the answer
                cleaned_answer = re.sub(
                    r"\n*SOURCES:\s*\[.*?\]\s*$", "", answer, flags=re.DOTALL
                ).strip()

                # Validate and fix citation numbers
                cleaned_answer = self._validate_and_fix_citation_numbers(
                    cleaned_answer, len(sources)
                )

                logger.debug(
                    f"Extracted {len(sources)} sources from SOURCES section and removed it from answer"
                )
                return sources, cleaned_answer

            except (json.JSONDecodeError, Exception) as e:
                logger.debug(f"Failed to parse SOURCES section: {e}")

        # Fallback to pattern matching for inline citations
        citation_pattern = r"\(([^,]+),\s*([^)]+)\)"
        matches = re.findall(citation_pattern, answer)

        for match in matches:
            author, work = match
            sources.append(
                {
                    "citation": f"{author.strip()}, {work.strip()}",
                    "record_id": "",  # Would need to be extracted from tool usage
                    "link": f"https://www.ccel.org/search?q={author.strip().replace(' ', '+')}",
                }
            )

        logger.debug(f"Extracted {len(sources)} sources from citation patterns")
        return sources, cleaned_answer

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history from memory."""
        history = []
        try:
            messages = self.memory.chat_memory.messages
            for message in messages:
                if isinstance(message, HumanMessage):
                    # Extract text from content (handles both string and list formats)
                    content = self._extract_text_from_content(message.content)
                    history.append({"role": "user", "content": content})
                elif isinstance(message, AIMessage):
                    # Extract text from content (handles both string and list formats)
                    content = self._extract_text_from_content(message.content)
                    history.append({"role": "assistant", "content": content})

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")

        return history

    def reset_conversation(self):
        """Reset the conversation memory."""
        self.memory.clear()
        logger.debug("Conversation memory cleared")
