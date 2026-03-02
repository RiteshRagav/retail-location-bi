"""
AgentOps Logging Layer: Structured execution tracking for multi-agent system.

This module provides lightweight, production-safe logging for agent execution,
capturing metrics like execution time, input/output payloads, and status.
Logs are persisted to both console and JSON file for observability.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


# Default log file location
LOG_FILE_PATH = Path(__file__).parent.parent / "agent_logs.json"


def log_agent_execution(
    agent_name: str,
    inputs: Dict[str, Any],
    outputs: Any,
    execution_time_ms: float,
    status: str = "success",
    error_message: Optional[str] = None
) -> None:
    """
    Log structured execution data for an agent.
    
    This function records agent execution for observability and debugging.
    It safely logs to both console and persistent JSON file.
    
    Args:
        agent_name: Name of the agent (e.g., "demand_agent")
        inputs: Dictionary of input parameters passed to the agent
        outputs: Output/return value from the agent
        execution_time_ms: Time taken for execution in milliseconds
        status: Execution status - "success" or "error"
        error_message: Optional error message if status is "error"
    
    Returns:
        None
    """
    
    # Construct structured log entry
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent_name": agent_name,
        "input_payload": _serialize_for_json(inputs),
        "output_payload": _serialize_for_json(outputs),
        "execution_time_ms": round(execution_time_ms, 2),
        "status": status,
        "error_message": error_message
    }
    
    try:
        # Log to console for real-time visibility
        _log_to_console(log_entry)
        
        # Append to JSON file for persistence
        _log_to_json_file(log_entry)
    
    except Exception as e:
        # Silently fail logging to prevent breaking main application
        # In production, you'd send this to a secondary error handler
        print(f"[WARNING] Failed to write agent log: {str(e)}")


def _log_to_console(log_entry: Dict[str, Any]) -> None:
    """
    Print structured log entry to console in readable format.
    
    Args:
        log_entry: Dictionary containing log data
    """
    status_emoji = "✓" if log_entry["status"] == "success" else "✗"
    
    print(
        f"{status_emoji} [{log_entry['timestamp']}] "
        f"Agent: {log_entry['agent_name']} | "
        f"Time: {log_entry['execution_time_ms']}ms | "
        f"Status: {log_entry['status']}"
    )


def _log_to_json_file(log_entry: Dict[str, Any]) -> None:
    """
    Append structured log entry to persistent JSON file.
    
    Creates the log file if it doesn't exist. Each entry is on its own line
    (JSONL format) for streaming/real-time log processing.
    
    Args:
        log_entry: Dictionary containing log data
    """
    try:
        # Ensure parent directory exists
        LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Append log entry as JSON line
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    except IOError as e:
        # Logging failure should not crash application
        raise IOError(f"Failed to write to log file {LOG_FILE_PATH}: {str(e)}")


def _serialize_for_json(obj: Any) -> Any:
    """
    Safely convert objects to JSON-serializable format.
    
    Handles common non-serializable types by converting them to strings.
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON-serializable version of the object
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_serialize_for_json(item) for item in obj]
    else:
        # Fallback: convert to string representation
        return str(obj)


def get_log_file_path() -> Path:
    """
    Get the path to the agent logs file.
    
    Returns:
        Path object pointing to agent_logs.json
    """
    return LOG_FILE_PATH
