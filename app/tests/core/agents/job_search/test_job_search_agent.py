"""
Tests for the Job Search Agent implementation.
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
    ENHANCED_SEARCH_REQUEST,
    RESUME_MATCH_REQUEST,
)
from app.core.agents.message_bus.message_bus import MessageBus
from backend.services.job_search.sources.base_source import BaseJobSource


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
def job_search_agent(message_bus, mock_job_source):
    """Create and configure a job search agent for testing."""
    agent = JobSearchAgent("test_job_search", source=mock_job_source)
    return agent


@pytest.mark.asyncio
async def test_agent_initialization(job_search_agent, message_bus):
    """Test agent initialization and topic subscription."""
    await job_search_agent.register_with_message_bus(message_bus)
    await job_search_agent.start()

    # Verify topic subscriptions
    assert JOB_SEARCH_TOPIC in job_search_agent.subscribed_topics
    assert JOB_MATCH_TOPIC in job_search_agent.subscribed_topics

    await job_search_agent.stop()


@pytest.mark.asyncio
async def test_basic_search_request(job_search_agent, message_bus):
    """Test handling of basic job search requests."""
    await job_search_agent.register_with_message_bus(message_bus)
    await job_search_agent.start()

    # Create a search request message
    search_request = Message.create(
        message_type=MessageType.EVENT,
        sender_id="test_sender",
        topic=JOB_SEARCH_TOPIC,
        payload={
            "type": SEARCH_REQUEST,
            "params": {
                "keywords": "python developer",
                "location": "San Francisco",
                "remote": True,
            },
        },
        priority=MessagePriority.NORMAL,
    )

    # Send the request
    await message_bus.publish(search_request)

    # Wait for processing
    await asyncio.sleep(0.1)

    # Get the results message
    results_message = None
    async for msg in message_bus.get_messages("test_sender"):
        if msg.topic == JOB_RESULTS_TOPIC:
            results_message = msg
            break

    assert results_message is not None
    assert "results" in results_message.payload
    assert "jobs" in results_message.payload["results"]

    await job_search_agent.stop()


@pytest.mark.asyncio
async def test_enhanced_search_request(job_search_agent, message_bus):
    """Test handling of enhanced job search requests."""
    await job_search_agent.register_with_message_bus(message_bus)
    await job_search_agent.start()

    # First save some user preferences
    preferences_cmd = Message.create(
        message_type=MessageType.COMMAND,
        sender_id="test_sender",
        topic="direct",
        payload={
            "command": "save_preferences",
            "user_id": "test_user",
            "preferences": {
                "technicalSkills": ["Python", "React", "AWS"],
                "jobTypes": ["Remote", "Full-time"],
                "careerGoals": "Senior Software Engineer position",
            },
        },
        priority=MessagePriority.NORMAL,
    )

    await message_bus.send_direct(preferences_cmd, job_search_agent.agent_id)
    await asyncio.sleep(0.1)

    # Create an enhanced search request
    search_request = Message.create(
        message_type=MessageType.EVENT,
        sender_id="test_sender",
        topic=JOB_SEARCH_TOPIC,
        payload={
            "type": ENHANCED_SEARCH_REQUEST,
            "params": {
                "user_id": "test_user",
                "keywords": "software engineer",
                "location": "Remote",
            },
        },
        priority=MessagePriority.NORMAL,
    )

    # Send the request
    await message_bus.publish(search_request)
    await asyncio.sleep(0.1)

    # Get the results message
    results_message = None
    async for msg in message_bus.get_messages("test_sender"):
        if msg.topic == JOB_RESULTS_TOPIC:
            results_message = msg
            break

    assert results_message is not None
    assert "results" in results_message.payload
    assert "jobs" in results_message.payload["results"]
    assert "preferences_used" in results_message.payload["results"]["metadata"]
    assert results_message.payload["results"]["metadata"]["preferences_used"] is True

    await job_search_agent.stop()


@pytest.mark.asyncio
async def test_resume_match_request(job_search_agent, message_bus):
    """Test handling of resume match analysis requests."""
    await job_search_agent.register_with_message_bus(message_bus)
    await job_search_agent.start()

    # Create a resume match request
    match_request = Message.create(
        message_type=MessageType.EVENT,
        sender_id="test_sender",
        topic=JOB_MATCH_TOPIC,
        payload={
            "type": RESUME_MATCH_REQUEST,
            "params": {
                "job_description": "Senior Python Developer position...",
                "resume_text": "Experienced software engineer with Python...",
            },
        },
        priority=MessagePriority.NORMAL,
    )

    # Send the request
    await message_bus.publish(match_request)
    await asyncio.sleep(0.1)

    # Get the response message
    response_message = None
    async for msg in message_bus.get_messages("test_sender"):
        if msg.message_type == MessageType.RESPONSE:
            response_message = msg
            break

    assert response_message is not None
    assert "match_score" in response_message.payload
    assert "analysis" in response_message.payload

    await job_search_agent.stop()


@pytest.mark.asyncio
async def test_error_handling(job_search_agent, message_bus):
    """Test error handling for invalid requests."""
    await job_search_agent.register_with_message_bus(message_bus)
    await job_search_agent.start()

    # Create an invalid search request (missing keywords)
    invalid_request = Message.create(
        message_type=MessageType.EVENT,
        sender_id="test_sender",
        topic=JOB_SEARCH_TOPIC,
        payload={
            "type": SEARCH_REQUEST,
            "params": {
                "location": "San Francisco",
            },
        },
        priority=MessagePriority.NORMAL,
    )

    # Send the request
    await message_bus.publish(invalid_request)
    await asyncio.sleep(0.1)

    # Get the error message
    error_message = None
    async for msg in message_bus.get_messages("test_sender"):
        if msg.message_type == MessageType.ERROR:
            error_message = msg
            break

    assert error_message is not None
    assert "error" in error_message.payload
    assert "Keywords are required" in error_message.payload["error"]

    await job_search_agent.stop()


@pytest.mark.asyncio
async def test_source_management_commands(job_search_agent, message_bus):
    """Test job source management commands."""
    await job_search_agent.register_with_message_bus(message_bus)
    await job_search_agent.start()

    # Test enabling a source
    enable_cmd = Message.create(
        message_type=MessageType.COMMAND,
        sender_id="test_sender",
        topic="direct",
        payload={
            "command": "enable_source",
            "source_name": "perplexity",
        },
        priority=MessagePriority.NORMAL,
    )

    await message_bus.send_direct(enable_cmd, job_search_agent.agent_id)
    await asyncio.sleep(0.1)

    # Get the response
    response = None
    async for msg in message_bus.get_messages("test_sender"):
        if msg.message_type == MessageType.RESPONSE:
            response = msg
            break

    assert response is not None
    assert response.payload["status"] == "success"

    # Test updating source priority
    update_cmd = Message.create(
        message_type=MessageType.COMMAND,
        sender_id="test_sender",
        topic="direct",
        payload={
            "command": "update_source_priority",
            "source_name": "perplexity",
            "priority": 20,
        },
        priority=MessagePriority.NORMAL,
    )

    await message_bus.send_direct(update_cmd, job_search_agent.agent_id)
    await asyncio.sleep(0.1)

    # Get the response
    response = None
    async for msg in message_bus.get_messages("test_sender"):
        if msg.message_type == MessageType.RESPONSE:
            response = msg
            break

    assert response is not None
    assert response.payload["status"] == "success"

    await job_search_agent.stop()
