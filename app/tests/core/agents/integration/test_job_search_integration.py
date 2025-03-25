"""
Integration tests for the Job Search Agent with other system agents.
"""

import pytest
import asyncio
from datetime import datetime
from typing import List, Dict, Any, AsyncGenerator

from app.core.agents import Message, MessageType, MessagePriority
from app.core.agents.job_search.job_search_agent import (
    JobSearchAgent,
    JOB_SEARCH_TOPIC,
    JOB_RESULTS_TOPIC,
    JOB_MATCH_TOPIC,
    SEARCH_REQUEST,
)
from app.tests.conftest import TestAgent
from app.core.agents.message_bus.message_bus import MessageBus
from app.tests.utils import wait_for_condition, wait_for_message
from backend.services.job_search.sources.base_source import BaseJobSource


async def cleanup_agent(agent: TestAgent, name: str, timeout: float = 2.0):
    """Helper function to clean up an agent."""
    if agent.is_running:
        await agent.stop()
        stopped = await wait_for_condition(
            lambda: not agent.is_running, timeout=timeout
        )
        assert stopped, f"{name} agent did not stop correctly"


class CareerCoachAgent(TestAgent):
    """Mock Career Coach Agent for testing integration."""

    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.received_job_results = []

    async def start(self):
        await super().start()
        await self.subscribe_to_topic(JOB_RESULTS_TOPIC)

    async def _handle_event(self, message: Message):
        await super()._handle_event(message)
        if message.topic == JOB_RESULTS_TOPIC:
            self.received_job_results.append(message.payload)


class DocumentAgent(TestAgent):
    """Mock Document Agent for testing integration."""

    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.resume_text = "Experienced software engineer with Python and AWS..."

    async def _handle_command(self, message: Message):
        await super()._handle_command(message)
        if message.payload.get("command") == "get_resume":
            response = Message.create(
                message_type=MessageType.RESPONSE,
                sender_id=self.agent_id,
                topic="direct",
                payload={"resume_text": self.resume_text},
                recipient_id=message.sender_id,
                priority=MessagePriority.NORMAL,
                in_response_to=message.message_id,
            )
            await self.send_message(response)


class MockJobSource(BaseJobSource):
    """Mock job source for testing."""

    def __init__(self):
        self.jobs = []
        self.search_called = False
        self.match_called = False

    async def search(
        self, query: str, filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Mock search method."""
        self.search_called = True
        return [
            {
                "title": "Software Engineer",
                "company": "Test Company",
                "location": "Remote",
                "description": "Test job description",
                "url": "https://example.com/job/1",
                "source": "mock",
            }
        ]

    async def match_resume(
        self, resume_text: str, job_description: str
    ) -> Dict[str, Any]:
        """Mock resume matching method."""
        self.match_called = True
        return {
            "match_score": 0.85,
            "analysis": "Test analysis",
            "recommendations": ["Test recommendation"],
        }


@pytest.fixture
def mock_job_source():
    """Create a mock job source for testing."""
    return MockJobSource()


@pytest.fixture
async def job_search_agent(
    message_bus, mock_job_source
) -> AsyncGenerator[JobSearchAgent, None]:
    """Create and configure a job search agent for testing."""
    agent = JobSearchAgent("job_search_1", source=mock_job_source)
    try:
        await agent.register_with_message_bus(message_bus)
        await agent.start()
        yield agent
    finally:
        await cleanup_agent(agent, "job_search")


@pytest.fixture
async def career_coach_agent(message_bus) -> AsyncGenerator[CareerCoachAgent, None]:
    """Create and configure a career coach agent for testing."""
    agent = CareerCoachAgent("career_coach_1")
    try:
        await agent.register_with_message_bus(message_bus)
        await agent.start()
        yield agent
    finally:
        await cleanup_agent(agent, "career_coach")


@pytest.fixture
async def document_agent(message_bus) -> AsyncGenerator[DocumentAgent, None]:
    """Create and configure a document agent for testing."""
    agent = DocumentAgent("document_1")
    try:
        await agent.register_with_message_bus(message_bus)
        await agent.start()
        yield agent
    finally:
        await cleanup_agent(agent, "document")


@pytest.mark.asyncio
@pytest.mark.timeout(15)  # Increased timeout for integration tests
async def test_career_coach_integration(
    job_search_agent, career_coach_agent, message_bus
):
    """Test integration between Job Search and Career Coach agents."""
    try:
        # Save user preferences through job search agent
        preferences_cmd = Message.create(
            message_type=MessageType.COMMAND,
            sender_id="career_coach_1",
            topic="direct",
            payload={
                "command": "save_preferences",
                "user_id": "test_user",
                "preferences": {
                    "technicalSkills": ["Python", "AWS", "React"],
                    "jobTypes": ["Remote", "Full-time"],
                    "careerGoals": "Senior Software Engineer position",
                },
            },
            recipient_id=job_search_agent.agent_id,
            priority=MessagePriority.NORMAL,
        )

        await message_bus.send_direct(preferences_cmd, job_search_agent.agent_id)

        # Wait for preferences to be saved
        assert await wait_for_condition(
            lambda: hasattr(job_search_agent, "user_preferences")
            and job_search_agent.user_preferences.get("test_user") is not None,
            timeout=5.0,
        ), "Timeout waiting for preferences to be saved"

        # Career coach initiates a job search
        search_request = Message.create(
            message_type=MessageType.EVENT,
            sender_id="career_coach_1",
            topic=JOB_SEARCH_TOPIC,
            payload={
                "type": SEARCH_REQUEST,
                "params": {
                    "keywords": "senior software engineer",
                    "location": "Remote",
                    "remote": True,
                },
            },
            priority=MessagePriority.NORMAL,
        )

        await message_bus.publish(search_request)

        # Wait for job results with assertion
        assert await wait_for_condition(
            lambda: len(career_coach_agent.received_job_results) > 0,
            timeout=5.0,
        ), "Timeout waiting for job results"

        # Verify job results content
        job_results = career_coach_agent.received_job_results[0]
        assert "results" in job_results, "Results not found in payload"
        assert "metadata" in job_results, "Metadata not found in payload"

    finally:
        # Cleanup handled by fixtures
        pass


@pytest.mark.asyncio
@pytest.mark.timeout(15)  # Increased timeout for integration tests
async def test_document_agent_integration(
    job_search_agent, document_agent, message_bus
):
    """Test integration between Job Search and Document agents."""
    try:
        # Create a job description
        job_description = """
        Senior Python Developer
        Requirements:
        - 5+ years Python experience
        - AWS cloud infrastructure
        - Experience with microservices
        """

        # Request resume match analysis
        match_request = Message.create(
            message_type=MessageType.EVENT,
            sender_id="document_1",
            topic=JOB_MATCH_TOPIC,
            payload={
                "type": "resume_match_request",
                "params": {
                    "job_description": job_description,
                    "resume_text": document_agent.resume_text,
                },
            },
            priority=MessagePriority.NORMAL,
        )

        await message_bus.publish(match_request)

        # Wait for match results with timeout
        match_results = await wait_for_message(
            message_bus, "document_1", message_type=MessageType.RESPONSE, timeout=5.0
        )

        # Verify the match results
        assert match_results is not None, "Timeout waiting for match results"
        assert (
            "match_score" in match_results.payload
        ), "Match score not found in results"
        assert "analysis" in match_results.payload, "Analysis not found in results"

    finally:
        # Cleanup handled by fixtures
        pass


@pytest.mark.asyncio
@pytest.mark.timeout(20)  # Increased timeout for this complex test
async def test_multi_agent_workflow(message_bus, mock_job_source):
    """Test complete workflow involving multiple agents."""
    job_search = None
    career_coach = None
    document_agent = None

    try:
        # Create and setup agents
        job_search = JobSearchAgent("job_search_3", source=mock_job_source)
        career_coach = CareerCoachAgent("career_coach_2")
        document_agent = DocumentAgent("document_2")

        # Clear message queues before starting test
        await message_bus.clear_all_queues()

        # Setup and start agents
        for agent in [job_search, career_coach, document_agent]:
            await agent.register_with_message_bus(message_bus)
            await agent.start()

        # 1. Career coach saves user preferences
        preferences_cmd = Message.create(
            message_type=MessageType.COMMAND,
            sender_id="career_coach_2",
            topic="direct",
            payload={
                "command": "save_preferences",
                "user_id": "test_user",
                "preferences": {
                    "technicalSkills": ["Python", "AWS", "React"],
                    "jobTypes": ["Remote", "Full-time"],
                    "careerGoals": "Senior Software Engineer position",
                },
            },
            recipient_id=job_search.agent_id,
            priority=MessagePriority.NORMAL,
        )

        await message_bus.send_direct(preferences_cmd, job_search.agent_id)

        # Wait for preferences to be saved with assertion
        assert await wait_for_condition(
            lambda: hasattr(job_search, "user_preferences")
            and job_search.user_preferences.get("test_user") is not None,
            timeout=5.0,
        ), "Timeout waiting for preferences to be saved"

        # 2. Career coach initiates job search
        search_request = Message.create(
            message_type=MessageType.EVENT,
            sender_id="career_coach_2",
            topic=JOB_SEARCH_TOPIC,
            payload={
                "type": SEARCH_REQUEST,
                "params": {
                    "keywords": "senior software engineer",
                    "location": "Remote",
                    "remote": True,
                },
            },
            priority=MessagePriority.NORMAL,
        )

        await message_bus.publish(search_request)

        # Wait for job results with assertion
        assert await wait_for_condition(
            lambda: len(career_coach.received_job_results) > 0,
            timeout=5.0,
        ), "Timeout waiting for job results"

        # Verify job results structure and content
        job_results = career_coach.received_job_results[0]
        assert "results" in job_results, "Results not found in payload"
        assert "metadata" in job_results, "Metadata not found in payload"
        assert isinstance(job_results["results"], list), "Results should be a list"

    finally:
        # Cleanup agents in reverse order
        for agent, name in [
            (document_agent, "document"),
            (career_coach, "career_coach"),
            (job_search, "job_search"),
        ]:
            if agent:
                await cleanup_agent(agent, name)

        if message_bus:
            try:
                await message_bus.clear_all_queues()
            except Exception as e:
                pytest.fail(f"Failed to clear message bus queues: {str(e)}")
