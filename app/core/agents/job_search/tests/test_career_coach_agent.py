"""
Unit tests for the CareerCoachAgent.

Tests cover:
1. Agent initialization and setup
2. Message handling
3. Input validation
4. Service integration
5. Error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from ..career_coach_agent import CareerCoachAgent, ValidationError
from ...message_bus import Message, MessageBus, MessageType
from ...protocols.agent_protocol import AgentStatus, AgentCapability

# Test data
MOCK_USER_ID = "test_user_123"
MOCK_SESSION_ID = "test_session_456"
MOCK_MESSAGE = "Hello, career coach!"
MOCK_CV_TEXT = "Professional CV with more than 50 characters for testing validation."


@pytest.fixture
def message_bus():
    """Create a mock message bus."""
    bus = Mock(spec=MessageBus)
    bus.register_agent = AsyncMock(return_value=True)
    bus.unregister_agent = AsyncMock(return_value=True)
    bus.publish = AsyncMock(return_value=True)
    return bus


@pytest.fixture
def mock_service():
    """Create a mock career coach service."""
    service = Mock()
    service.create_session.return_value = {"session_id": MOCK_SESSION_ID}
    service.process_message.return_value = {"response": "Mock response"}
    service.analyze_cv.return_value = {"analysis": "Mock analysis"}
    service.generate_roadmap.return_value = {"roadmap": "Mock roadmap"}
    service.get_session_summary.return_value = {"summary": "Mock summary"}
    return service


@pytest.fixture
async def agent(message_bus, mock_service):
    """Create a CareerCoachAgent instance with mocked dependencies."""
    with patch(
        "backend.services.career_coach.career_coach_agent.CareerCoachAgent",
        return_value=mock_service,
    ):
        agent = CareerCoachAgent(message_bus)
        await agent.initialize()
        yield agent
        await agent.shutdown()


class TestCareerCoachAgentInitialization:
    """Test agent initialization and setup."""

    async def test_initialization(self, agent, message_bus):
        """Test that agent initializes correctly."""
        assert agent.agent_type == "career_coach"
        assert agent.status == AgentStatus.READY
        assert len(agent.capabilities) == 4
        message_bus.register_agent.assert_called_once()

    async def test_capabilities_registration(self, agent):
        """Test that all capabilities are registered correctly."""
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
        message = Message(
            message_id="test_id",
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
        message = Message(
            message_id="test_id",
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
        message = Message(
            message_id="test_id",
            message_type=MessageType.COMMAND,
            sender_id="test_sender",
            topic="career.cv.analyze",
            payload={"session_id": MOCK_SESSION_ID, "cv_text": MOCK_CV_TEXT},
        )

        result = await agent.handle_message(message)

        assert result["status"] == "success"
        assert "analysis" in result["data"]
        mock_service.analyze_cv.assert_called_once_with(MOCK_SESSION_ID, MOCK_CV_TEXT)


class TestValidation:
    """Test input validation."""

    @pytest.mark.parametrize(
        "field_name,value,expected_error",
        [
            ("user_id", "", "user_id cannot be empty"),
            ("user_id", None, "user_id must be a string"),
            ("message", "", "message cannot be empty"),
            ("cv_text", "short", "cv_text cannot be empty"),
            ("session_id", 123, "session_id must be a string"),
        ],
    )
    async def test_validation_errors(self, agent, field_name, value, expected_error):
        """Test that validation errors are raised for invalid inputs."""
        with pytest.raises(ValidationError) as exc_info:
            agent._validate_string_field(
                field_name, value, 50 if field_name == "cv_text" else 1
            )
        assert str(exc_info.value) == expected_error

    async def test_empty_cv_validation(self, agent):
        """Test that CV text has minimum length requirement."""
        message = Message(
            message_id="test_id",
            message_type=MessageType.COMMAND,
            sender_id="test_sender",
            topic="career.cv.analyze",
            payload={"session_id": MOCK_SESSION_ID, "cv_text": "too short"},
        )

        result = await agent.handle_message(message)
        assert result["status"] == "error"
        assert result["error_type"] == "validation"


class TestErrorHandling:
    """Test error handling scenarios."""

    async def test_service_error_handling(self, agent, mock_service):
        """Test handling of service errors."""
        mock_service.create_session.side_effect = Exception("Service error")

        message = Message(
            message_id="test_id",
            message_type=MessageType.COMMAND,
            sender_id="test_sender",
            topic="career.session.create",
            payload={"user_id": MOCK_USER_ID},
        )

        result = await agent.handle_message(message)
        assert result["status"] == "error"
        assert result["error_type"] == "internal"
        assert "Service error" in result["message"]

    async def test_unsupported_message_type(self, agent):
        """Test handling of unsupported message types."""
        message = Message(
            message_id="test_id",
            message_type="INVALID_TYPE",
            sender_id="test_sender",
            topic="career.session.create",
            payload={},
        )

        result = await agent.handle_message(message)
        assert result["status"] == "error"
        assert "Unsupported message type" in result["message"]

    async def test_unsupported_topic(self, agent):
        """Test handling of unsupported topics."""
        message = Message(
            message_id="test_id",
            message_type=MessageType.COMMAND,
            sender_id="test_sender",
            topic="unsupported.topic",
            payload={},
        )

        result = await agent.handle_message(message)
        assert result["status"] == "error"
        assert "Unsupported command topic" in result["message"]
