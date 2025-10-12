"""Custom LiteLLM callback to log traces to JSONL file."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from litellm.integrations.custom_logger import CustomLogger


class TraceLogger(CustomLogger):
    """Logs LiteLLM traces to JSONL file for ProdLens ingestion."""

    def __init__(self):
        super().__init__()
        self.log_dir = Path(os.environ.get("LITELLM_LOG_DIR", ".prod-lens/logs"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "litellm-traces.jsonl"

    def log_success_event(self, kwargs: Dict[str, Any], response_obj: Any, start_time: float, end_time: float):
        """Log successful completion to JSONL."""
        try:
            # Extract usage information
            usage = {}
            if hasattr(response_obj, "usage"):
                usage_obj = response_obj.usage
                usage = {
                    "prompt_tokens": getattr(usage_obj, "prompt_tokens", 0),
                    "completion_tokens": getattr(usage_obj, "completion_tokens", 0),
                    "total_tokens": getattr(usage_obj, "total_tokens", 0),
                }

            # Build trace record
            record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "model": kwargs.get("model"),
                "call_type": kwargs.get("call_type", "completion"),
                "usage": usage,
                "latency_ms": (end_time - start_time) * 1000,
                "status": "success",
                "status_code": 200,
                "metadata": kwargs.get("metadata", {}),
            }

            # Add optional fields
            if "litellm_params" in kwargs:
                litellm_params = kwargs["litellm_params"]
                if "metadata" in litellm_params and "user_api_key_user_id" in litellm_params["metadata"]:
                    record["developer_id"] = litellm_params["metadata"]["user_api_key_user_id"]

            # Write to JSONL
            with open(self.log_file, "a") as f:
                f.write(json.dumps(record) + "\n")

        except Exception as e:
            print(f"[TraceLogger] Error logging success: {e}")

    def log_failure_event(self, kwargs: Dict[str, Any], response_obj: Any, start_time: float, end_time: float):
        """Log failed completion to JSONL."""
        try:
            record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "model": kwargs.get("model"),
                "call_type": kwargs.get("call_type", "completion"),
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "latency_ms": (end_time - start_time) * 1000,
                "status": "failure",
                "status_code": 500,
                "error": str(response_obj) if response_obj else "Unknown error",
                "metadata": kwargs.get("metadata", {}),
            }

            with open(self.log_file, "a") as f:
                f.write(json.dumps(record) + "\n")

        except Exception as e:
            print(f"[TraceLogger] Error logging failure: {e}")


# Initialize logger instance
trace_logger = TraceLogger()
