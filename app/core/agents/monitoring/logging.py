import json
import logging
import logging.config
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class AgentLogFormatter(logging.Formatter):
    """Custom formatter for agent logs"""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record"""
        # Add timestamp in ISO format
        record.timestamp = datetime.fromtimestamp(record.created).isoformat()

        # Extract agent context if available
        agent_id = getattr(record, "agent_id", None)
        agent_type = getattr(record, "agent_type", None)

        # Create base log entry
        log_entry = {
            "timestamp": record.timestamp,
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add agent context if available
        if agent_id:
            log_entry["agent_id"] = agent_id
        if agent_type:
            log_entry["agent_type"] = agent_type

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)


def setup_logging(
    log_level: str = "INFO", log_dir: Optional[str] = None, console: bool = True
) -> None:
    """Setup logging configuration"""

    handlers = {}

    # Console handler
    if console:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "formatter": "agent_formatter",
            "stream": "ext://sys.stdout",
        }

    # File handler
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "agent_formatter",
            "filename": str(log_path / "agent.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        }

    # Create logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"agent_formatter": {"()": AgentLogFormatter}},
        "handlers": handlers,
        "loggers": {
            "agent": {
                "level": log_level,
                "handlers": list(handlers.keys()),
                "propagate": False,
            }
        },
    }

    # Apply configuration
    logging.config.dictConfig(config)


class AgentLogger:
    """Logger wrapper for agents"""

    def __init__(self, agent_id: str, agent_type: str):
        self.logger = logging.getLogger("agent")
        self.agent_id = agent_id
        self.agent_type = agent_type

    def _log(
        self,
        level: int,
        msg: str,
        extra_fields: Optional[Dict[str, Any]] = None,
        *args,
        **kwargs
    ):
        """Internal logging method"""
        extra = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "extra_fields": extra_fields or {},
        }
        self.logger.log(level, msg, extra=extra, *args, **kwargs)

    def debug(
        self, msg: str, extra_fields: Optional[Dict[str, Any]] = None, *args, **kwargs
    ):
        """Log debug message"""
        self._log(logging.DEBUG, msg, extra_fields, *args, **kwargs)

    def info(
        self, msg: str, extra_fields: Optional[Dict[str, Any]] = None, *args, **kwargs
    ):
        """Log info message"""
        self._log(logging.INFO, msg, extra_fields, *args, **kwargs)

    def warning(
        self, msg: str, extra_fields: Optional[Dict[str, Any]] = None, *args, **kwargs
    ):
        """Log warning message"""
        self._log(logging.WARNING, msg, extra_fields, *args, **kwargs)

    def error(
        self, msg: str, extra_fields: Optional[Dict[str, Any]] = None, *args, **kwargs
    ):
        """Log error message"""
        self._log(logging.ERROR, msg, extra_fields, *args, **kwargs)

    def critical(
        self, msg: str, extra_fields: Optional[Dict[str, Any]] = None, *args, **kwargs
    ):
        """Log critical message"""
        self._log(logging.CRITICAL, msg, extra_fields, *args, **kwargs)
