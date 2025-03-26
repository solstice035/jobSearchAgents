"""
Tests for the Job Search Agent implementation.
"""

import pytest
import pytest_asyncio
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
        self.last_query = None
        self.last_filters = None

    async def search(
        self, query: str, filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Mock search method."""
        self.search_called = True
        self.last_query = query
        self.last_filters = filters

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


@pytest_asyncio.fixture
async def job_search_agent(message_bus, mock_job_source):
    """Create and configure a job search agent for testing."""
    # Create the agent but don't start the run loop
    agent = JobSearchAgent("test_job_search", source=mock_job_source)
    try:
        await agent.register_with_message_bus(message_bus)

        # Subscribe to required topics
        await agent.subscribe_to_topic(JOB_SEARCH_TOPIC)
        await agent.subscribe_to_topic(JOB_MATCH_TOPIC)

        # Instead of running the agent loop, we'll manually handle messages in the tests
        agent._running = True  # Pretend it's running
        yield agent
    finally:
        # Clean up
        agent._running = False
        await message_bus.unregister_agent(agent.agent_id)
        await message_bus.clear_all_queues()


@pytest.mark.asyncio
@pytest.mark.timeout(2)  # Add explicit timeout
async def test_agent_initialization(job_search_agent, message_bus):
    """Test agent initialization and topic subscription."""
    # Verify topic subscriptions
    assert JOB_SEARCH_TOPIC in job_search_agent.subscribed_topics
    assert JOB_MATCH_TOPIC in job_search_agent.subscribed_topics

    # Force ensure the agent is stopped to prevent hanging
    await job_search_agent.stop()
    await message_bus.clear_all_queues()


@pytest.mark.asyncio
@pytest.mark.timeout(3)  # Increased timeout
async def test_basic_search_request(job_search_agent, message_bus):
    """Test handling of basic job search requests."""
    # Start the agent
    await job_search_agent.start()

    # Make sure test_sender is registered with the message bus
    await message_bus.register_agent("test_sender")

    # Create a test agent to subscribe to the results topic
    class TestResultsHandler:
        def __init__(self, agent_id):
            self.agent_id = agent_id
            self.received_messages = []

        async def handle_message(self, message):
            self.received_messages.append(message)

    test_handler = TestResultsHandler("test_sender")
    await message_bus.subscribe(JOB_RESULTS_TOPIC, test_handler.handle_message)

    # Clear any existing messages
    async for _ in message_bus.get_messages("test_sender"):
        pass

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

    # Wait for message processing
    processed = await job_search_agent.wait_for_message_processed(timeout=2.0)
    assert processed, "Message was not processed within timeout"

    # Get all messages for test_sender
    results_message = None
    direct_response = None

    async for msg in message_bus.get_messages("test_sender"):
        if msg.topic == JOB_RESULTS_TOPIC:
            results_message = msg
        elif msg.topic == "direct" and msg.message_type == MessageType.RESPONSE:
            direct_response = msg

    # Stop the agent
    await job_search_agent.stop()

    # Check topic message
    assert results_message is not None, "No results message received on topic"
    assert "results" in results_message.payload, "Results not found in payload"
    assert "metadata" in results_message.payload, "Metadata not found in payload"

    # Check direct response
    assert direct_response is not None, "No direct response received"
    assert "results" in direct_response.payload, "Results not found in direct response"
    assert (
        "metadata" in direct_response.payload
    ), "Metadata not found in direct response"


@pytest.mark.asyncio
@pytest.mark.timeout(3)  # Increased timeout
async def test_enhanced_search_request(job_search_agent, message_bus):
    """Test handling of enhanced job search requests."""
    # Start the agent
    await job_search_agent.start()

    # Clear any existing messages
    async for _ in message_bus.get_messages("test_sender"):
        pass

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
                "softSkills": ["Communication", "Leadership"],
                "industries": ["Technology", "Finance"],
                "jobTypes": ["Full-time", "Remote"],
                "experienceLevel": "Senior",
            },
        },
        priority=MessagePriority.NORMAL,
        recipient_id=job_search_agent.agent_id,
    )

    await message_bus.send_direct(preferences_cmd, job_search_agent.agent_id)
    processed = await job_search_agent.wait_for_message_processed(timeout=2.0)
    assert processed, "Preferences command was not processed within timeout"

    # Now send an enhanced search request
    search_request = Message.create(
        message_type=MessageType.EVENT,
        sender_id="test_sender",
        topic=JOB_SEARCH_TOPIC,
        payload={
            "type": ENHANCED_SEARCH_REQUEST,
            "params": {
                "user_id": "test_user",
                "base_query": "senior software engineer",
            },
        },
        priority=MessagePriority.NORMAL,
    )

    await message_bus.publish(search_request)
    processed = await job_search_agent.wait_for_message_processed(timeout=2.0)
    assert processed, "Search request was not processed within timeout"

    # Get all messages for test_sender
    results_message = None
    direct_response = None

    async for msg in message_bus.get_messages("test_sender"):
        if msg.topic == JOB_RESULTS_TOPIC:
            results_message = msg
        elif msg.topic == "direct" and msg.message_type == MessageType.RESPONSE:
            direct_response = msg

    # Stop the agent
    await job_search_agent.stop()

    # Check results
    assert results_message is not None, "No results message received"
    assert "results" in results_message.payload
    assert "metadata" in results_message.payload
    assert "preferences_applied" in results_message.payload["metadata"]


@pytest.mark.asyncio
@pytest.mark.timeout(3)  # Added timeout
async def test_resume_match_request(job_search_agent, message_bus):
    """Test handling of resume match analysis requests."""
    # Start the agent
    await job_search_agent.start()

    # Clear any existing messages
    async for _ in message_bus.get_messages("test_sender"):
        pass

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
    processed = await job_search_agent.wait_for_message_processed(timeout=2.0)
    assert processed, "Resume match request was not processed within timeout"

    # Get all messages for test_sender
    response_message = None

    async for msg in message_bus.get_messages("test_sender"):
        if msg.message_type == MessageType.RESPONSE:
            response_message = msg
            break

    # Stop the agent
    await job_search_agent.stop()

    # Check response
    assert response_message is not None, "No response message received"
    assert "match_score" in response_message.payload
    assert "analysis" in response_message.payload
    assert "recommendations" in response_message.payload


@pytest.mark.asyncio
@pytest.mark.timeout(3)  # Added timeout
async def test_error_handling(job_search_agent, message_bus):
    """Test error handling for invalid requests."""
    # Start the agent
    await job_search_agent.start()

    # Clear any existing messages
    async for _ in message_bus.get_messages("test_sender"):
        pass

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
    processed = await job_search_agent.wait_for_message_processed(timeout=2.0)
    assert processed, "Invalid request was not processed within timeout"

    # Get all messages for test_sender
    error_message = None

    async for msg in message_bus.get_messages("test_sender"):
        if msg.message_type == MessageType.ERROR:
            error_message = msg
            break

    # Stop the agent
    await job_search_agent.stop()

    # Check error message
    assert error_message is not None, "No error message received"
    assert "error" in error_message.payload
    assert "details" in error_message.payload


@pytest.mark.asyncio
@pytest.mark.timeout(3)  # Added timeout
async def test_source_management_commands(job_search_agent, message_bus):
    """Test job source management commands."""
    # Start the agent
    await job_search_agent.start()

    # Clear any existing messages
    async for _ in message_bus.get_messages("test_sender"):
        pass

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
        recipient_id=job_search_agent.agent_id,
    )

    await message_bus.send_direct(enable_cmd, job_search_agent.agent_id)
    processed = await job_search_agent.wait_for_message_processed(timeout=2.0)
    assert processed, "Enable source command was not processed within timeout"

    # Get all messages for test_sender
    response = None

    async for msg in message_bus.get_messages("test_sender"):
        if msg.message_type == MessageType.RESPONSE:
            response = msg
            break

    # Stop the agent
    await job_search_agent.stop()

    # Check response
    assert response is not None, "No response received for enable source command"
    assert "status" in response.payload
    assert response.payload["status"] == "success"
