"""
Source formatting utilities for standardizing and deduplicating sources.

This module provides shared functionality for formatting sources from different
RAG approaches into a consistent format.
"""

import logging
from typing import List, Dict, Any, Optional

from ...infrastructure.parsers.response_handler import generate_ccel_url, deduplicate_sources

logger = logging.getLogger(__name__)


class SourceFormatter:
    """
    Handles formatting and standardization of sources from different RAG systems.
    """

    @staticmethod
    def format_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Format sources into standardized format with links and deduplication.

        Args:
            sources: List of source dictionaries with citation and record_id

        Returns:
            List of formatted source dictionaries with record_id, link, and citation_text
        """
        formatted_sources = []

        for source in sources:
            record_id = source.get("record_id", "")
            citation_text = source.get("citation", "")
            existing_link = source.get("link", "")

            # Generate CCEL link if we have a record_id but no existing link
            if record_id and not existing_link:
                link = generate_ccel_url(record_id)
            elif existing_link:
                link = existing_link
            else:
                # Fallback to search link if we have citation but no record_id
                link = f"https://www.ccel.org/search?q={citation_text.replace(' ', '+')}" if citation_text else ""

            # Only include sources that have meaningful content
            if citation_text or record_id:
                formatted_sources.append({
                    "record_id": record_id,
                    "link": link,
                    "citation_text": citation_text
                })

        # Remove duplicates using existing utility
        return deduplicate_sources(formatted_sources)

    @staticmethod
    def format_agent_sources(agent_sources: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Format sources specifically from agent responses.

        Args:
            agent_sources: Sources from theological agent

        Returns:
            List of formatted source dictionaries
        """
        formatted_sources = []

        for source in agent_sources:
            citation = source.get("citation", "")
            record_id = source.get("record_id", "")
            link = source.get("link", "")

            # Generate CCEL link if we have a record_id but no link
            if record_id and not link:
                link = generate_ccel_url(record_id)

            if citation or record_id:
                formatted_sources.append({
                    "record_id": record_id,
                    "link": link or f"https://www.ccel.org/search?q={citation.replace(' ', '+')}",
                    "citation_text": citation
                })

        return deduplicate_sources(formatted_sources)

    @staticmethod
    def format_structured_sources(structured_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Format sources from structured AI response data.

        Args:
            structured_data: Structured response from AI with sources

        Returns:
            List of formatted source dictionaries
        """
        sources = structured_data.get('sources', [])
        return SourceFormatter.format_sources(sources)

    @staticmethod
    def log_source_stats(sources: List[Dict[str, str]], context: str = ""):
        """
        Log statistics about formatted sources.

        Args:
            sources: Formatted sources to log stats for
            context: Context string for logging
        """
        context_str = f" ({context})" if context else ""
        logger.debug(f"Formatted {len(sources)} unique sources{context_str}")

        if sources:
            with_record_ids = sum(1 for s in sources if s.get("record_id"))
            with_links = sum(1 for s in sources if s.get("link"))
            logger.debug(f"Sources: {with_record_ids} with record IDs, {with_links} with links")