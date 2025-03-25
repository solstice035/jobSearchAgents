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
        self.user_preferences = {}  # Store user preferences in memory

    async def start(self):
        """Start the agent and subscribe to relevant topics."""
        await super().start()
        await self.subscribe_to_topic(JOB_SEARCH_TOPIC)
        await self.subscribe_to_topic(JOB_MATCH_TOPIC)

    async def handle_message(self, message: Message):
        """Handle incoming messages."""
        try:
            if message.message_type == MessageType.COMMAND:
                await self._handle_command(message)
            elif message.message_type == MessageType.EVENT:
                await self._handle_event(message)
            else:
                await self._send_error_response(
                    message, f"Unsupported message type: {message.message_type}"
                )
        except Exception as e:
            await self._send_error_response(
                message, f"Error handling message: {str(e)}"
            )

    async def _handle_command(self, message: Message):
        """Handle command messages."""
        command = message.payload.get("command")
        if not command:
            await self._send_error_response(message, "No command specified")
            return

        try:
            if command == "save_preferences":
                user_id = message.payload.get("user_id")
                preferences = message.payload.get("preferences")
                if not user_id or not preferences:
                    await self._send_error_response(
                        message, "User ID and preferences required"
                    )
                    return

                self.user_preferences[user_id] = preferences
                await self._send_response(
                    message, {"status": "success", "message": "Preferences saved"}
                )

            elif command == "enable_source":
                source_name = message.payload.get("source_name")
                if not source_name:
                    await self._send_error_response(message, "Source name required")
                    return

                # Enable the source in the service
                self.service.enable_source(source_name)
                await self._send_response(
                    message,
                    {"status": "success", "message": f"Source {source_name} enabled"},
                )

            elif command == "update_source_priority":
                source_name = message.payload.get("source_name")
                priority = message.payload.get("priority")
                if not source_name or priority is None:
                    await self._send_error_response(
                        message, "Source name and priority required"
                    )
                    return

                # Update source priority in the service
                self.service.update_source_priority(source_name, priority)
                await self._send_response(
                    message,
                    {
                        "status": "success",
                        "message": f"Priority updated for {source_name}",
                    },
                )

            else:
                await self._send_error_response(message, f"Unknown command: {command}")

        except Exception as e:
            await self._send_error_response(message, str(e))

    async def _handle_event(self, message: Message):
        """Handle event messages."""
        event_type = message.payload.get("type")
        if not event_type:
            await self._send_error_response(message, "No event type specified")
            return

        try:
            if event_type == SEARCH_REQUEST:
                await self._handle_search_request(message)
            elif event_type == ENHANCED_SEARCH_REQUEST:
                await self._handle_enhanced_search_request(message)
            elif event_type == RESUME_MATCH_REQUEST:
                await self._handle_resume_match_request(message)
            else:
                await self._send_error_response(
                    message, f"Unknown event type: {event_type}"
                )

        except Exception as e:
            await self._send_error_response(message, str(e))

    async def _handle_search_request(self, message: Message):
        """Handle basic job search request."""
        params = message.payload.get("params", {})

        # Validate required parameters
        if "keywords" not in params:
            await self._send_error_response(message, "Keywords are required")
            return

        try:
            # Perform the search
            jobs = await self.service.search(
                query=params["keywords"],
                location=params.get("location"),
                filters={
                    "remote": params.get("remote", False),
                    "recency": params.get("recency"),
                    "experience_level": params.get("experience_level"),
                },
            )

            # Format results
            response = {
                "results": jobs,  # Direct list of jobs
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "search_criteria": params,
                },
            }

            # Send results to both the results topic and as a direct response
            await self._publish_results(response, message)
            await self._send_response(message, response)

        except Exception as e:
            await self._send_error_response(message, f"Search failed: {str(e)}")

    async def _handle_enhanced_search_request(self, message: Message):
        """Handle enhanced job search request."""
        params = message.payload.get("params", {})

        # Validate required parameters
        if "keywords" not in params or "user_id" not in params:
            await self._send_error_response(
                message, "Keywords and user_id are required"
            )
            return

        try:
            # Get user preferences
            user_id = params["user_id"]
            preferences = self.user_preferences.get(user_id, {})

            # Enhance search with preferences
            enhanced_query = self._enhance_search_query(params["keywords"], preferences)

            # Perform the search
            jobs = await self.service.search(
                query=enhanced_query,
                location=params.get("location"),
                filters={
                    "remote": params.get("remote", False),
                    "recency": params.get("recency"),
                    "experience_level": params.get("experience_level"),
                },
            )

            # Format results
            response = {
                "results": jobs,  # Direct list of jobs
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "search_criteria": params,
                    "preferences_used": bool(preferences),
                    "enhanced_query": enhanced_query,
                },
            }

            # Send results to both the results topic and as a direct response
            await self._publish_results(response, message)
            await self._send_response(message, response)

        except Exception as e:
            await self._send_error_response(
                message, f"Enhanced search failed: {str(e)}"
            )

    async def _handle_resume_match_request(self, message: Message):
        """Handle resume match request."""
        params = message.payload.get("params", {})

        # Validate required parameters
        if "job_description" not in params or "resume_text" not in params:
            await self._send_error_response(
                message, "Job description and resume text are required"
            )
            return

        try:
            # Perform the match analysis
            match_results = await self.service.match_resume(
                resume_text=params["resume_text"],
                job_description=params["job_description"],
            )

            # Send response
            await self._send_response(message, match_results)

        except Exception as e:
            await self._send_error_response(message, f"Resume match failed: {str(e)}")

    def _enhance_search_query(
        self, base_query: str, preferences: Dict[str, Any]
    ) -> str:
        """Enhance the search query with user preferences."""
        if not preferences:
            return base_query

        enhanced_parts = [base_query]

        # Add relevant skills
        if "technicalSkills" in preferences:
            relevant_skills = [
                skill
                for skill in preferences["technicalSkills"][:3]
                if skill.lower() not in base_query.lower()
            ]
            if relevant_skills:
                enhanced_parts.append(f"with skills in {', '.join(relevant_skills)}")

        # Add job type preferences
        if "jobTypes" in preferences:
            job_types = [jt for jt in preferences["jobTypes"] if jt.lower() != "remote"]
            if job_types:
                enhanced_parts.append(f"looking for {' or '.join(job_types)}")

        return " ".join(enhanced_parts)

    async def _publish_results(
        self, results: Dict[str, Any], original_message: Message
    ):
        """Publish results to the results topic."""
        response = Message.create(
            message_type=MessageType.EVENT,
            sender_id=self.agent_id,
            topic=JOB_RESULTS_TOPIC,
            payload=results,
            priority=MessagePriority.NORMAL,
            correlation_id=str(original_message.message_id),
        )
        await self.message_bus.publish(response)

    async def _send_response(
        self, original_message: Message, response_data: Dict[str, Any]
    ):
        """Send a direct response message."""
        response = Message.create(
            message_type=MessageType.RESPONSE,
            sender_id=self.agent_id,
            topic="direct",
            payload=response_data,
            priority=MessagePriority.NORMAL,
            recipient_id=original_message.sender_id,
            correlation_id=str(original_message.message_id),
        )
        await self.message_bus.send_direct(response, original_message.sender_id)

    async def _send_error_response(self, original_message: Message, error_message: str):
        """Send an error response message."""
        response = Message.create(
            message_type=MessageType.ERROR,
            sender_id=self.agent_id,
            topic="direct",
            payload={"error": error_message},
            priority=MessagePriority.HIGH,
            recipient_id=original_message.sender_id,
            correlation_id=str(original_message.message_id),
        )
        await self.message_bus.send_direct(response, original_message.sender_id)

    async def _handle_response(self, message: Message):
        """Handle response messages."""
        # By default, we don't need to handle responses
        pass

    async def _handle_error(self, message: Message):
        """Handle error messages."""
        # By default, we don't need to handle errors
        pass
