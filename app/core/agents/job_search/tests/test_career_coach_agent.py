"""
Unit tests for the CareerCoachAgent.

Tests cover:
1. Agent initialization and setup
2. Message handling
3. Input validation
4. Service integration
5. Error handling
"""

import os
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.core.agents.job_search.career_coach_agent import (
    CareerCoachAgent,
    ValidationError,
)
from app.core.agents.message_bus import Message, MessageBus, MessageType
from app.core.agents.protocols.agent_protocol import AgentStatus, AgentCapability

# Test data
MOCK_USER_ID = "test_user_123"
MOCK_SESSION_ID = "test_session_456"
MOCK_MESSAGE = "Hello, career coach!"
MOCK_CV_TEXT = "Professional CV with more than 50 characters for testing validation."
MOCK_API_KEY = "test-api-key-123"


@pytest.fixture(autouse=True)
def mock_env():
    """Mock environment variables."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": MOCK_API_KEY}):
        yield


@pytest.fixture
def mock_service():
    """Create a mock CareerCoachService."""
    service = Mock()
    service.create_session.return_value = {"session_id": MOCK_SESSION_ID}
    service.process_message.return_value = {
        "response": "Mock response",
        "session_id": MOCK_SESSION_ID,
        "current_phase": "initial",
    }
    service.analyze_cv.return_value = {
        "analysis": {"skills": [], "experience": []},
        "session_id": MOCK_SESSION_ID,
    }
    return service


@pytest.fixture
async def message_bus():
    """Create a mock message bus."""
    return AsyncMock(spec=MessageBus)


@pytest.fixture
async def agent(message_bus, mock_service):
    """Create a CareerCoachAgent instance for testing."""
    with patch(
        "app.core.agents.job_search.career_coach_agent.CareerCoachService"
    ) as mock_service_class:
        mock_service_class.return_value = mock_service
        agent = CareerCoachAgent(message_bus)
        await agent.initialize()
        yield agent


class TestAgentInitialization:
    """Test agent initialization and setup."""

    async def test_initialization(self, agent):
        """Test that agent initializes correctly."""
        assert agent.agent_id == "career_coach"
        assert agent.status == AgentStatus.READY

    async def test_capabilities_registration(self, agent):
        """Test that agent registers all required capabilities."""
        capability_names = {cap.name for cap in agent.capabilities}
        expected_names = {
            "create_coaching_session",
            "process_message",
            "analyze_cv",
            "generate_roadmap",
        }
        assert capability_names == expected_names

    async def test_topic_subscriptions(self, agent):
        """Test that agent subscribes to all required topics."""
        expected_topics = {
            "career.session.create",
            "career.session.message",
            "career.cv.analyze",
            "career.roadmap.generate",
        }
        assert agent.subscribed_topics == expected_topics


class TestMessageHandling:
    """Test message handling functionality."""

    async def test_create_session(self, agent, mock_service):
        """Test handling of create session command."""
        message = Message.create(
            message_type=MessageType.COMMAND,
            sender_id="test_sender",
            topic="career.session.create",
            payload={"user_id": MOCK_USER_ID},
        )

        result = await agent.handle_message(message)

        assert result["status"] == "success"
        assert result["data"]["session_id"] == MOCK_SESSION_ID
        mock_service.create_session.assert_called_once_with(MOCK_USER_ID)

    async def test_process_message(self, agent, mock_service):
        """Test handling of process message command."""
        message = Message.create(
            message_type=MessageType.COMMAND,
            sender_id="test_sender",
            topic="career.session.message",
            payload={"session_id": MOCK_SESSION_ID, "message": MOCK_MESSAGE},
        )

        result = await agent.handle_message(message)

        assert result["status"] == "success"
        assert "response" in result["data"]
        mock_service.process_message.assert_called_once_with(
            MOCK_SESSION_ID, MOCK_MESSAGE
        )

    async def test_analyze_cv(self, agent, mock_service):
        """Test handling of CV analysis command."""
        message = Message.create(
            message_type=MessageType.COMMAND,
            sender_id="test_sender",
            topic="career.cv.analyze",
            payload={"session_id": MOCK_SESSION_ID, "cv_text": MOCK_CV_TEXT},
        )

        result = await agent.handle_message(message)

        assert result["status"] == "success"
        assert "analysis" in result["data"]
        mock_service.analyze_cv.assert_called_once_with(MOCK_SESSION_ID, MOCK_CV_TEXT)

    async def test_empty_cv_validation(self, agent):
        """Test validation of empty CV text."""
        message = Message.create(
            message_type=MessageType.COMMAND,
            sender_id="test_sender",
            topic="career.cv.analyze",
            payload={"session_id": MOCK_SESSION_ID, "cv_text": ""},
        )

        result = await agent.handle_message(message)

        assert result["status"] == "error"
        assert "validation" in result["error_type"]

    async def test_service_error_handling(self, agent, mock_service):
        """Test handling of service errors."""
        mock_service.process_message.side_effect = ValueError("Session not found")

        message = Message.create(
            message_type=MessageType.COMMAND,
            sender_id="test_sender",
            topic="career.session.message",
            payload={"session_id": "invalid_session", "message": MOCK_MESSAGE},
        )

        result = await agent.handle_message(message)

        assert result["status"] == "error"
        assert "Session not found" in result["message"]

    async def test_unsupported_message_type(self, agent):
        """Test handling of unsupported message type."""
        message = Message.create(
            message_type=MessageType.EVENT,
            sender_id="test_sender",
            topic="career.session.message",
            payload={"session_id": MOCK_SESSION_ID, "message": MOCK_MESSAGE},
        )

        result = await agent.handle_message(message)

        assert result["status"] == "error"
        assert "Unsupported message type" in result["message"]

    async def test_unsupported_topic(self, agent):
        """Test handling of unsupported topic."""
        message = Message.create(
            message_type=MessageType.COMMAND,
            sender_id="test_sender",
            topic="career.invalid.topic",
            payload={"session_id": MOCK_SESSION_ID},
        )

        result = await agent.handle_message(message)

        assert result["status"] == "error"
        assert "Unsupported command topic" in result["message"]
