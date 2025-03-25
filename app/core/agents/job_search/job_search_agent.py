"""
Job Search Agent implementation that integrates with the agent framework.

This agent handles job search operations and coordinates with other agents
in the system through the message bus.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from app.core.agents import BaseAgent, Message, MessageType, MessagePriority
from app.core.agents.monitoring import MESSAGES_PROCESSED, PROCESSING_TIME
from backend.services.job_search.job_search_service import JobSearchService
from backend.services.job_search.sources.base_source import BaseJobSource

# Message topics
JOB_SEARCH_TOPIC = "job_search"
JOB_RESULTS_TOPIC = "job_results"
JOB_MATCH_TOPIC = "job_match"

# Message types
SEARCH_REQUEST = "search_request"
ENHANCED_SEARCH_REQUEST = "enhanced_search_request"
RESUME_MATCH_REQUEST = "resume_match_request"


class JobSearchAgent(BaseAgent):
    """
    Agent that handles job search operations and coordinates with other agents.

    This agent wraps the existing JobSearchService and adds message-based
    communication capabilities.
    """

    def __init__(
        self,
        agent_id: str,
        config_file: Optional[str] = None,
        source: Optional[BaseJobSource] = None,
    ):
        """
        Initialize the Job Search Agent.

        Args:
            agent_id: Unique identifier for this agent instance
            config_file: Optional path to job source configuration file
            source: Optional job source to use
        """
        super().__init__(agent_id, "job_search")
        self.service = JobSearchService(config_file, source)

    async def start(self):
        """Start the agent and subscribe to relevant topics."""
        await super().start()

        # Subscribe to job search related topics
        await self.subscribe_to_topic(JOB_SEARCH_TOPIC)
        await self.subscribe_to_topic(JOB_MATCH_TOPIC)

    async def _handle_command(self, message: Message):
        """
        Handle incoming command messages.

        Args:
            message: The command message to process
        """
        await super()._handle_command(message)

        command = message.payload.get("command")
        if not command:
            self.logger.warning("Received command message without command field")
            return

        try:
            if command == "enable_source":
                source_name = message.payload.get("source_name")
                if source_name:
                    result = self.service.enable_source(source_name)
                    await self._send_response(message, result)

            elif command == "disable_source":
                source_name = message.payload.get("source_name")
                if source_name:
                    result = self.service.disable_source(source_name)
                    await self._send_response(message, result)

            elif command == "update_source_priority":
                source_name = message.payload.get("source_name")
                priority = message.payload.get("priority")
                if source_name and priority is not None:
                    result = self.service.update_source_priority(source_name, priority)
                    await self._send_response(message, result)

            elif command == "save_preferences":
                user_id = message.payload.get("user_id")
                preferences = message.payload.get("preferences")
                if user_id and preferences:
                    result = self.service.save_user_preferences(user_id, preferences)
                    await self._send_response(message, result)

            else:
                self.logger.warning(f"Unknown command: {command}")

        except Exception as e:
            self.logger.error(f"Error processing command {command}: {str(e)}")
            await self._send_error_response(message, str(e))

    async def _handle_event(self, message: Message):
        """
        Handle incoming event messages.

        Args:
            message: The event message to process
        """
        await super()._handle_event(message)

        event_type = message.payload.get("type")
        if not event_type:
            self.logger.warning("Received event message without type field")
            return

        try:
            if event_type == SEARCH_REQUEST:
                await self._handle_search_request(message)

            elif event_type == ENHANCED_SEARCH_REQUEST:
                await self._handle_enhanced_search_request(message)

            elif event_type == RESUME_MATCH_REQUEST:
                await self._handle_resume_match_request(message)

            else:
                self.logger.warning(f"Unknown event type: {event_type}")

        except Exception as e:
            self.logger.error(f"Error processing event {event_type}: {str(e)}")
            await self._send_error_response(message, str(e))

    async def _handle_search_request(self, message: Message):
        """Handle a basic job search request."""
        params = message.payload.get("params", {})

        # Extract search parameters
        keywords = params.get("keywords")
        if not keywords:
            await self._send_error_response(message, "Keywords are required")
            return

        # Perform the search
        results = self.service.search_jobs(
            keywords=keywords,
            location=params.get("location"),
            recency=params.get("recency"),
            experience_level=params.get("experience_level"),
            remote=params.get("remote", False),
            source_name=params.get("source_name"),
            search_strategy=params.get("search_strategy", "primary"),
        )

        # Send results
        await self._publish_results(results, message)

    async def _handle_enhanced_search_request(self, message: Message):
        """Handle an enhanced job search request."""
        params = message.payload.get("params", {})

        # Extract required parameters
        user_id = params.get("user_id")
        keywords = params.get("keywords")
        if not user_id or not keywords:
            await self._send_error_response(
                message, "User ID and keywords are required"
            )
            return

        # Perform enhanced search
        results = self.service.enhanced_job_search(
            user_id=user_id,
            keywords=keywords,
            location=params.get("location"),
            recency=params.get("recency"),
            experience_level=params.get("experience_level"),
            remote=params.get("remote", False),
            source_name=params.get("source_name"),
            search_strategy=params.get("search_strategy", "primary"),
        )

        # Send results
        await self._publish_results(results, message)

    async def _handle_resume_match_request(self, message: Message):
        """Handle a resume match analysis request."""
        params = message.payload.get("params", {})

        # Extract required parameters
        job_description = params.get("job_description")
        resume_text = params.get("resume_text")
        if not job_description or not resume_text:
            await self._send_error_response(
                message, "Job description and resume text are required"
            )
            return

        # Perform analysis
        results = self.service.analyze_resume_match(
            job_description=job_description, resume_text=resume_text
        )

        # Send results
        await self._send_response(message, results)

    async def _publish_results(
        self, results: Dict[str, Any], original_message: Message
    ):
        """Publish job search results."""
        message = Message.create(
            message_type=MessageType.EVENT,
            sender_id=self.agent_id,
            topic=JOB_RESULTS_TOPIC,
            payload={
                "results": results,
                "original_request": original_message.payload,
                "request_id": str(original_message.message_id),
            },
            priority=MessagePriority.NORMAL,
        )

        await self.send_message(message, topic=JOB_RESULTS_TOPIC)

    async def _send_response(
        self, original_message: Message, response_data: Dict[str, Any]
    ):
        """Send a direct response message."""
        message = Message.create(
            message_type=MessageType.RESPONSE,
            sender_id=self.agent_id,
            topic="direct",
            payload=response_data,
            recipient_id=original_message.sender_id,
            priority=MessagePriority.NORMAL,
            in_response_to=original_message.message_id,
        )

        await self.send_message(message)

    async def _send_error_response(self, original_message: Message, error_message: str):
        """Send an error response message."""
        message = Message.create(
            message_type=MessageType.ERROR,
            sender_id=self.agent_id,
            topic="direct",
            payload={"error": error_message},
            recipient_id=original_message.sender_id,
            priority=MessagePriority.HIGH,
            in_response_to=original_message.message_id,
        )

        await self.send_message(message)
