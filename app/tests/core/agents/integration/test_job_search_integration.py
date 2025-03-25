"""
Integration tests for the Job Search Agent with other system agents.
"""

import pytest
import asyncio
from datetime import datetime
from typing import List, Dict, Any

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
from backend.services.job_search.sources.base_source import BaseJobSource


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


@pytest.mark.asyncio
async def test_career_coach_integration(message_bus, monitor_manager, mock_job_source):
    """Test integration between Job Search and Career Coach agents."""
    # Create and setup agents
    job_search = JobSearchAgent("job_search_1", source=mock_job_source)
    career_coach = CareerCoachAgent("career_coach_1")

    await job_search.register_with_message_bus(message_bus)
    await career_coach.register_with_message_bus(message_bus)

    await job_search.start()
    await career_coach.start()

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
        priority=MessagePriority.NORMAL,
    )

    await message_bus.send_direct(preferences_cmd, job_search.agent_id)
    await asyncio.sleep(0.1)

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
    await asyncio.sleep(0.1)

    # Verify career coach received the results
    assert len(career_coach.received_job_results) > 0
    results = career_coach.received_job_results[0]
    assert "results" in results
    assert "jobs" in results["results"]

    # Cleanup
    await job_search.stop()
    await career_coach.stop()


@pytest.mark.asyncio
async def test_document_agent_integration(
    message_bus, monitor_manager, mock_job_source
):
    """Test integration between Job Search and Document agents."""
    # Create and setup agents
    job_search = JobSearchAgent("job_search_2", source=mock_job_source)
    document_agent = DocumentAgent("document_1")

    await job_search.register_with_message_bus(message_bus)
    await document_agent.register_with_message_bus(message_bus)

    await job_search.start()
    await document_agent.start()

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
    await asyncio.sleep(0.1)

    # Get the response
    response = None
    async for msg in message_bus.get_messages("document_1"):
        if msg.message_type == MessageType.RESPONSE:
            response = msg
            break

    assert response is not None
    assert "match_score" in response.payload
    assert "analysis" in response.payload

    # Cleanup
    await job_search.stop()
    await document_agent.stop()


@pytest.mark.asyncio
async def test_multi_agent_workflow(message_bus, monitor_manager, mock_job_source):
    """Test complete workflow involving multiple agents."""
    # Create and setup agents
    job_search = JobSearchAgent("job_search_3", source=mock_job_source)
    career_coach = CareerCoachAgent("career_coach_2")
    document_agent = DocumentAgent("document_2")

    await job_search.register_with_message_bus(message_bus)
    await career_coach.register_with_message_bus(message_bus)
    await document_agent.register_with_message_bus(message_bus)

    await job_search.start()
    await career_coach.start()
    await document_agent.start()

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
        priority=MessagePriority.NORMAL,
    )

    await message_bus.send_direct(preferences_cmd, job_search.agent_id)
    await asyncio.sleep(0.1)

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
    await asyncio.sleep(0.1)

    # 3. For each job in results, document agent requests match analysis
    assert len(career_coach.received_job_results) > 0
    jobs = career_coach.received_job_results[0]["results"]["jobs"]

    for job in jobs[:1]:  # Test with first job only
        match_request = Message.create(
            message_type=MessageType.EVENT,
            sender_id="document_2",
            topic=JOB_MATCH_TOPIC,
            payload={
                "type": "resume_match_request",
                "params": {
                    "job_description": job.get("description", ""),
                    "resume_text": document_agent.resume_text,
                },
            },
            priority=MessagePriority.NORMAL,
        )

        await message_bus.publish(match_request)
        await asyncio.sleep(0.1)

        # Verify match analysis response
        response = None
        async for msg in message_bus.get_messages("document_2"):
            if msg.message_type == MessageType.RESPONSE:
                response = msg
                break

        assert response is not None
        assert "match_score" in response.payload
        assert "analysis" in response.payload

    # Cleanup
    await job_search.stop()
    await career_coach.stop()
    await document_agent.stop()
