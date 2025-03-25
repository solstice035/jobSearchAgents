"""
Job Search Agent implementation that integrates with the agent framework.

This agent handles job search operations and coordinates with other agents
in the system through the message bus.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from app.core.agents import BaseAgent, Message, MessageType, MessagePriority, MessageBus
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
        source: Optional[BaseJobSource] = None,
        config_file: Optional[str] = None,
    ):
        """
        Initialize the Job Search Agent.

        Args:
            agent_id: Unique identifier for this agent instance
            source: Optional job source to use
            config_file: Optional path to job source configuration file
        """
        super().__init__(agent_type="job_search", message_bus=None)
        self.service = JobSearchService(config_file, source)
        self.user_preferences = {}  # Store user preferences in memory

    async def register_with_message_bus(self, message_bus: MessageBus) -> bool:
        """Register the agent with a message bus."""
        self._message_bus = message_bus
        return await self.initialize()

    async def stop(self) -> bool:
        """Stop the agent."""
        return await self.shutdown()

    async def start(self) -> None:
        """Start the agent's message processing loop."""
        await self.initialize()
        while self._running:
            try:
                message = await self._message_bus.get_next_message(
                    self.agent_id, timeout=0.1
                )
                if message:
                    await self.handle_message(message)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    async def initialize(self) -> bool:
        """Initialize the agent and subscribe to topics."""
        if await super().initialize():
            await self.subscribe_to_topic(JOB_SEARCH_TOPIC)
            await self.subscribe_to_topic(JOB_MATCH_TOPIC)
            return True
        return False

    async def _handle_command(self, message: Message) -> Dict[str, Any]:
        """Handle command messages."""
        command = message.payload.get("command")
        if not command:
            return {"error": "No command specified"}

        try:
            if command == "save_preferences":
                user_id = message.payload.get("user_id")
                preferences = message.payload.get("preferences")
                if not user_id or not preferences:
                    return {"error": "User ID and preferences required"}

                self.user_preferences[user_id] = preferences
                return {"status": "success", "message": "Preferences saved"}

            elif command == "enable_source":
                source_name = message.payload.get("source_name")
                if not source_name:
                    return {"error": "Source name required"}

                # Enable the source in the service
                self.service.enable_source(source_name)
                return {"status": "success", "message": f"Source {source_name} enabled"}

            elif command == "update_source_priority":
                source_name = message.payload.get("source_name")
                priority = message.payload.get("priority")
                if not source_name or priority is None:
                    return {"error": "Source name and priority required"}

                # Update source priority in the service
                self.service.update_source_priority(source_name, priority)
                return {
                    "status": "success",
                    "message": f"Priority updated for {source_name}",
                }

            return {"error": f"Unknown command: {command}"}

        except Exception as e:
            return {"error": f"Error handling command: {str(e)}"}

    async def _handle_event(self, message: Message) -> Dict[str, Any]:
        """Handle event messages."""
        event_type = message.payload.get("event_type")
        if not event_type:
            return {"error": "No event type specified"}

        try:
            if event_type == "search_request":
                return await self._handle_search_request(message)
            elif event_type == "enhanced_search_request":
                return await self._handle_enhanced_search_request(message)
            elif event_type == "resume_match_request":
                return await self._handle_resume_match_request(message)

            return {"error": f"Unknown event type: {event_type}"}

        except Exception as e:
            return {"error": f"Error handling event: {str(e)}"}

    async def _handle_search_request(self, message: Message) -> Dict[str, Any]:
        """Handle basic search request."""
        params = message.payload.get("params", {})

        if "query" not in params:
            return {"error": "Search query is required"}

        try:
            results = await self.service.search_jobs(
                query=params["query"],
                location=params.get("location"),
                job_type=params.get("job_type"),
                date_posted=params.get("date_posted"),
            )

            await self._publish_results(results, message)
            return {"status": "success", "message": "Search completed"}

        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}

    async def _handle_enhanced_search_request(self, message: Message) -> Dict[str, Any]:
        """Handle enhanced search request with user preferences."""
        params = message.payload.get("params", {})

        if "query" not in params or "user_id" not in params:
            return {"error": "Search query and user ID are required"}

        try:
            # Get user preferences
            preferences = self.user_preferences.get(params["user_id"], {})

            # Enhance query with preferences
            enhanced_query = self._enhance_search_query(params["query"], preferences)

            # Perform search
            results = await self.service.search_jobs(
                query=enhanced_query,
                location=params.get("location"),
                job_type=params.get("job_type"),
                date_posted=params.get("date_posted"),
            )

            await self._publish_results(results, message)
            return {"status": "success", "message": "Enhanced search completed"}

        except Exception as e:
            return {"error": f"Enhanced search failed: {str(e)}"}

    async def _handle_resume_match_request(self, message: Message) -> Dict[str, Any]:
        """Handle resume match request."""
        params = message.payload.get("params", {})

        if "job_description" not in params or "resume_text" not in params:
            return {"error": "Job description and resume text are required"}

        try:
            # Perform the match analysis
            match_results = await self.service.match_resume(
                resume_text=params["resume_text"],
                job_description=params["job_description"],
            )
            return match_results

        except Exception as e:
            return {"error": f"Resume match failed: {str(e)}"}

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
        await self._message_bus.publish(response)

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
        await self._message_bus.send_direct(response, original_message.sender_id)

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
        await self._message_bus.send_direct(response, original_message.sender_id)

    async def _handle_response(self, message: Message):
        """Handle response messages."""
        # By default, we don't need to handle responses
        pass

    async def _handle_error(self, message: Message):
        """Handle error messages."""
        # By default, we don't need to handle errors
        pass
