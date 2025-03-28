"""
Career Coach Agent

This module implements an agent wrapper around the CareerCoachService to provide
career guidance capabilities through the agent system.
"""

import asyncio
import logging
import functools
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from ..base_agent import BaseAgent
from ..protocols.agent_protocol import AgentCapability, AgentStatus
from ..message_bus import Message, MessageBus, MessageType
from backend.services.career_coach.career_coach_agent import (
    CareerCoachAgent as CareerCoachService,
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


class CareerCoachAgent(BaseAgent):
    """
    Agent that provides career coaching capabilities by wrapping the CareerCoachService.
    Handles career guidance requests through the agent messaging system.
    """

    def __init__(self, message_bus: MessageBus):
        """Initialize the career coach agent."""
        super().__init__("career_coach", message_bus)
        self.agent_id = "career_coach"  # Override UUID with fixed ID

        # Initialize the career coach service
        self.service = CareerCoachService()

        # Thread pool for running blocking service calls
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Register capabilities
        self._register_capabilities()

        # Set up command and query handlers
        self._setup_handlers()

    def _register_capabilities(self):
        """Register all agent capabilities."""
        capabilities = [
            AgentCapability(
                name="create_coaching_session",
                description="Create a new career coaching session",
                parameters={"user_id": "string"},
                required_resources=["openai_api"],
            ),
            AgentCapability(
                name="process_message",
                description="Process a message in an existing coaching session",
                parameters={"session_id": "string", "message": "string"},
                required_resources=["openai_api"],
            ),
            AgentCapability(
                name="analyze_cv",
                description="Analyze a CV and integrate insights into coaching session",
                parameters={"session_id": "string", "cv_text": "string"},
                required_resources=["openai_api", "cv_parser"],
            ),
            AgentCapability(
                name="generate_roadmap",
                description="Generate a personalized career roadmap",
                parameters={"session_id": "string"},
                required_resources=["openai_api"],
            ),
        ]

        for capability in capabilities:
            self.register_capability(capability)
            logger.debug(f"Registered capability: {capability.name}")

        # Subscribe to relevant topics
        self.topics = [
            "career.session.create",
            "career.session.message",
            "career.cv.analyze",
            "career.roadmap.generate",
        ]

    def _setup_handlers(self):
        """Set up command and query handlers using dispatch tables."""
        self._command_handlers = {
            "career.session.create": self._handle_create_session,
            "career.session.message": self._handle_process_message,
            "career.cv.analyze": self._handle_analyze_cv,
            "career.roadmap.generate": self._handle_generate_roadmap,
        }

        self._query_handlers = {
            "career.session.summary": self._handle_session_summary,
        }

    async def initialize(self) -> bool:
        """Initialize the agent and subscribe to topics."""
        try:
            success = await super().initialize()
            if not success:
                return False

            # Subscribe to all topics
            for topic in self.topics:
                await self.subscribe_to_topic(topic)
                logger.info(f"Subscribed to topic: {topic}")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}", exc_info=True)
            return False

    async def handle_message(self, message: Message) -> Dict[str, Any]:
        """Handle incoming messages based on type and topic."""
        try:
            logger.info(
                f"Handling message: type={message.message_type}, topic={message.topic}",
                extra={"message_id": message.message_id},
            )

            if message.message_type == MessageType.COMMAND:
                handler = self._command_handlers.get(message.topic)
                if not handler:
                    return {
                        "status": "error",
                        "message": f"Unsupported command topic: {message.topic}",
                        "error_type": "unsupported_topic",
                    }
                return await handler(message)

            elif message.message_type == MessageType.QUERY:
                handler = self._query_handlers.get(message.topic)
                if not handler:
                    return {
                        "status": "error",
                        "message": f"Unsupported query topic: {message.topic}",
                        "error_type": "unsupported_topic",
                    }
                return await handler(message)

            return {
                "status": "error",
                "message": f"Unsupported message type: {message.message_type}",
                "error_type": "unsupported_type",
            }

        except ValidationError as e:
            logger.warning(
                f"Validation error: {str(e)}", extra={"message_id": message.message_id}
            )
            return {"status": "error", "message": str(e), "error_type": "validation"}

        except Exception as e:
            logger.error(
                f"Error handling message: {str(e)}",
                exc_info=True,
                extra={"message_id": message.message_id},
            )
            return {"status": "error", "message": str(e), "error_type": "internal"}

    def _validate_string_field(
        self, field_name: str, value: Any, min_length: int = 1
    ) -> str:
        """Validate a string field."""
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")
        if len(value.strip()) < min_length:
            raise ValidationError(f"{field_name} cannot be empty")
        return value.strip()

    async def _run_in_executor(self, func: Callable, *args, **kwargs) -> Any:
        """Run a blocking function in the thread pool executor."""
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, functools.partial(func, *args, **kwargs)
        )

    async def _handle_create_session(self, message: Message) -> Dict[str, Any]:
        """Handle create session command."""
        try:
            user_id = self._validate_string_field(
                "user_id", message.payload.get("user_id")
            )

            logger.info(f"Creating coaching session for user: {user_id}")
            result = await self._run_in_executor(self.service.create_session, user_id)

            logger.info(f"Created coaching session: {result.get('session_id')}")
            return {"status": "success", "data": result}

        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            return {"status": "error", "message": str(e), "error_type": "validation"}
        except Exception as e:
            logger.error(f"Failed to create coaching session: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e), "error_type": "internal"}

    async def _handle_process_message(self, message: Message) -> Dict[str, Any]:
        """Handle process message command."""
        try:
            session_id = self._validate_string_field(
                "session_id", message.payload.get("session_id")
            )
            user_message = self._validate_string_field(
                "message", message.payload.get("message")
            )

            logger.info(f"Processing message for session: {session_id}")
            result = await self._run_in_executor(
                self.service.process_message, session_id, user_message
            )

            logger.debug(f"Message processed for session: {session_id}")
            return {"status": "success", "data": result}

        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            return {"status": "error", "message": str(e), "error_type": "validation"}
        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e), "error_type": "internal"}

    async def _handle_analyze_cv(self, message: Message) -> Dict[str, Any]:
        """Handle CV analysis command."""
        try:
            session_id = self._validate_string_field(
                "session_id", message.payload.get("session_id")
            )
            cv_text = self._validate_string_field(
                "cv_text", message.payload.get("cv_text"), min_length=50
            )

            logger.info(f"Analyzing CV for session: {session_id}")
            result = await self._run_in_executor(
                self.service.analyze_cv, session_id, cv_text
            )

            logger.info(f"CV analysis completed for session: {session_id}")
            return {"status": "success", "data": result}

        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            return {"status": "error", "message": str(e), "error_type": "validation"}
        except Exception as e:
            logger.error(f"Failed to analyze CV: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e), "error_type": "internal"}

    async def _handle_generate_roadmap(self, message: Message) -> Dict[str, Any]:
        """Handle roadmap generation command."""
        try:
            session_id = self._validate_string_field(
                "session_id", message.payload.get("session_id")
            )

            logger.info(f"Generating roadmap for session: {session_id}")
            result = await self._run_in_executor(
                self.service.generate_roadmap, session_id
            )

            logger.info(f"Roadmap generated for session: {session_id}")
            return {"status": "success", "data": result}

        except Exception as e:
            logger.error(f"Failed to generate roadmap: {str(e)}", exc_info=True)
            raise

    async def _handle_session_summary(self, message: Message) -> Dict[str, Any]:
        """Handle session summary query."""
        try:
            session_id = self._validate_string_field(
                "session_id", message.payload.get("session_id")
            )

            logger.info(f"Retrieving session summary: {session_id}")
            result = await self._run_in_executor(
                self.service.get_session_summary, session_id
            )

            logger.debug(f"Retrieved session summary: {session_id}")
            return {"status": "success", "data": result}

        except Exception as e:
            logger.error(f"Failed to get session summary: {str(e)}", exc_info=True)
            raise

    async def _handle_event(self, message: Message) -> Dict[str, Any]:
        """Handle event messages."""
        logger.debug(f"Received event message: {message.topic}")
        return {"status": "success"}

    async def _handle_error(self, message: Message) -> Dict[str, Any]:
        """Handle error messages."""
        logger.error(
            f"Received error message",
            extra={"message_id": message.message_id, "payload": message.payload},
        )
        return {"status": "acknowledged"}
