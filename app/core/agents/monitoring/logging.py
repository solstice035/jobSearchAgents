import json
import logging
import logging.config
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID


class JsonFormatter(logging.Formatter):
    """Format log records as JSON"""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.msg,
            "logger": record.name,
        }

        # Add agent info if present
        if hasattr(record, "agent_id"):
            log_entry["agent_id"] = record.agent_id
        if hasattr(record, "agent_type"):
            log_entry["agent_type"] = record.agent_type

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_entry["extra_fields"] = record.extra_fields

        # Convert UUIDs to strings
        def convert_uuids(obj):
            if isinstance(obj, dict):
                return {k: convert_uuids(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_uuids(v) for v in obj]
            elif isinstance(obj, UUID):
                return str(obj)
            return obj

        log_entry = convert_uuids(log_entry)
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
        "formatters": {"agent_formatter": {"()": JsonFormatter}},
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
