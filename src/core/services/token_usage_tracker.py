"""
Token Usage Tracker Service for tracking and persisting API token usage.

This service tracks input and output tokens from AI API calls,
storing daily aggregated statistics in a JSON file.
"""

import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

from ...config.settings import IS_DEVELOPMENT

logger = logging.getLogger(__name__)
if IS_DEVELOPMENT:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)


class TokenUsageTracker:
    """
    Tracks and persists token usage statistics by day.

    Thread-safe implementation using a lock for concurrent access.
    Data is stored in a JSON file and loaded on initialization.
    """

    _instance: Optional['TokenUsageTracker'] = None
    _lock = threading.Lock()

    def __new__(cls, data_dir: Optional[str] = None):
        """Singleton pattern to ensure single instance across the application."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the token usage tracker.

        Args:
            data_dir: Directory to store the usage data file.
                     Defaults to 'data' in the project root.
        """
        if self._initialized:
            return

        self._initialized = True
        self._write_lock = threading.Lock()

        # Set up data directory
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default to project root/data
            self.data_dir = Path(__file__).parent.parent.parent.parent / "data"

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data_file = self.data_dir / "token_usage.json"

        # Load existing data
        self._usage_data: Dict[str, Any] = self._load_data()

        logger.info(f"TokenUsageTracker initialized with data file: {self.data_file}")

    def _load_data(self) -> Dict[str, Any]:
        """Load usage data from JSON file."""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    logger.debug(f"Loaded token usage data with {len(data)} days")
                    return data
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading token usage data: {e}")

        return {}

    def _save_data(self):
        """Save usage data to JSON file."""
        try:
            with self._write_lock:
                with open(self.data_file, 'w') as f:
                    json.dump(self._usage_data, f, indent=2)
                logger.debug("Token usage data saved successfully")
        except IOError as e:
            logger.error(f"Error saving token usage data: {e}")

    def _get_today_key(self) -> str:
        """Get today's date as a string key (YYYY-MM-DD)."""
        return datetime.now().strftime("%Y-%m-%d")

    def _ensure_day_entry(self, date_key: str) -> Dict[str, Any]:
        """Ensure a day entry exists and return it."""
        if date_key not in self._usage_data:
            self._usage_data[date_key] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "requests": 0,
                "by_endpoint": {}
            }
        return self._usage_data[date_key]

    def record_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        endpoint: str = "unknown",
        model: str = "unknown"
    ):
        """
        Record token usage for a single API call.

        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            endpoint: API endpoint that made the call (e.g., "/query", "/query-agent")
            model: Model name used for the call
        """
        if input_tokens < 0 or output_tokens < 0:
            logger.warning(f"Invalid token counts: input={input_tokens}, output={output_tokens}")
            return

        date_key = self._get_today_key()
        total_tokens = input_tokens + output_tokens

        with self._write_lock:
            day_data = self._ensure_day_entry(date_key)

            # Update daily totals
            day_data["input_tokens"] += input_tokens
            day_data["output_tokens"] += output_tokens
            day_data["total_tokens"] += total_tokens
            day_data["requests"] += 1

            # Update per-endpoint stats
            if endpoint not in day_data["by_endpoint"]:
                day_data["by_endpoint"][endpoint] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "requests": 0,
                    "models": {}
                }

            endpoint_data = day_data["by_endpoint"][endpoint]
            endpoint_data["input_tokens"] += input_tokens
            endpoint_data["output_tokens"] += output_tokens
            endpoint_data["total_tokens"] += total_tokens
            endpoint_data["requests"] += 1

            # Track model usage
            if model not in endpoint_data["models"]:
                endpoint_data["models"][model] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "requests": 0
                }
            endpoint_data["models"][model]["input_tokens"] += input_tokens
            endpoint_data["models"][model]["output_tokens"] += output_tokens
            endpoint_data["models"][model]["requests"] += 1

        # Save after each update (could be optimized with batching)
        self._save_data()

        logger.debug(
            f"Recorded usage: {input_tokens} input, {output_tokens} output "
            f"for {endpoint} using {model}"
        )

    def get_usage_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get usage summary for the specified number of days.

        Args:
            days: Number of days to include in summary (default: 30)

        Returns:
            Dictionary with aggregated usage statistics
        """
        today = datetime.now()
        start_date = today - timedelta(days=days - 1)

        total_input = 0
        total_output = 0
        total_requests = 0
        endpoint_totals: Dict[str, Dict[str, int]] = {}
        model_totals: Dict[str, Dict[str, int]] = {}
        days_with_data = 0

        for i in range(days):
            date = start_date + timedelta(days=i)
            date_key = date.strftime("%Y-%m-%d")

            if date_key in self._usage_data:
                days_with_data += 1
                day_data = self._usage_data[date_key]
                total_input += day_data.get("input_tokens", 0)
                total_output += day_data.get("output_tokens", 0)
                total_requests += day_data.get("requests", 0)

                # Aggregate endpoint stats
                for endpoint, ep_data in day_data.get("by_endpoint", {}).items():
                    if endpoint not in endpoint_totals:
                        endpoint_totals[endpoint] = {
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "requests": 0
                        }
                    endpoint_totals[endpoint]["input_tokens"] += ep_data.get("input_tokens", 0)
                    endpoint_totals[endpoint]["output_tokens"] += ep_data.get("output_tokens", 0)
                    endpoint_totals[endpoint]["requests"] += ep_data.get("requests", 0)

                    # Aggregate model stats
                    for model, model_data in ep_data.get("models", {}).items():
                        if model not in model_totals:
                            model_totals[model] = {
                                "input_tokens": 0,
                                "output_tokens": 0,
                                "requests": 0
                            }
                        model_totals[model]["input_tokens"] += model_data.get("input_tokens", 0)
                        model_totals[model]["output_tokens"] += model_data.get("output_tokens", 0)
                        model_totals[model]["requests"] += model_data.get("requests", 0)

        return {
            "period": {
                "days": days,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": today.strftime("%Y-%m-%d"),
                "days_with_data": days_with_data
            },
            "totals": {
                "input_tokens": total_input,
                "output_tokens": total_output,
                "total_tokens": total_input + total_output,
                "requests": total_requests
            },
            "by_endpoint": endpoint_totals,
            "by_model": model_totals,
            "averages": {
                "tokens_per_day": (total_input + total_output) / days_with_data if days_with_data > 0 else 0,
                "requests_per_day": total_requests / days_with_data if days_with_data > 0 else 0,
                "tokens_per_request": (total_input + total_output) / total_requests if total_requests > 0 else 0
            }
        }

    def get_daily_breakdown(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get daily breakdown of token usage.

        Args:
            days: Number of days to include (default: 30)

        Returns:
            List of daily usage records, sorted by date descending
        """
        today = datetime.now()
        start_date = today - timedelta(days=days - 1)

        daily_data = []

        for i in range(days):
            date = start_date + timedelta(days=i)
            date_key = date.strftime("%Y-%m-%d")

            if date_key in self._usage_data:
                day_data = self._usage_data[date_key].copy()
                day_data["date"] = date_key
                daily_data.append(day_data)
            else:
                # Include empty days for completeness
                daily_data.append({
                    "date": date_key,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "requests": 0,
                    "by_endpoint": {}
                })

        # Sort by date descending (most recent first)
        daily_data.sort(key=lambda x: x["date"], reverse=True)

        return daily_data

    def get_today_usage(self) -> Dict[str, Any]:
        """Get today's usage statistics."""
        date_key = self._get_today_key()
        if date_key in self._usage_data:
            data = self._usage_data[date_key].copy()
            data["date"] = date_key
            return data

        return {
            "date": date_key,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "requests": 0,
            "by_endpoint": {}
        }

    def clear_old_data(self, keep_days: int = 90):
        """
        Remove data older than the specified number of days.

        Args:
            keep_days: Number of days of data to retain (default: 90)
        """
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        cutoff_key = cutoff_date.strftime("%Y-%m-%d")

        with self._write_lock:
            keys_to_remove = [
                key for key in self._usage_data.keys()
                if key < cutoff_key
            ]

            for key in keys_to_remove:
                del self._usage_data[key]

            if keys_to_remove:
                self._save_data()
                logger.info(f"Removed {len(keys_to_remove)} old usage records")


# Global instance getter
def get_token_tracker() -> TokenUsageTracker:
    """Get the global TokenUsageTracker instance."""
    return TokenUsageTracker()
