"""Integration tests for the agent system."""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import Optional

from app.tests.conftest import TestAgent
from app.core.agents import (
    BaseAgent,
    Message,
    MessageType,
    MessagePriority,
    MessageBus,
    MESSAGES_PROCESSED,
    MESSAGES_SENT,
    PROCESSING_TIME,
    QUEUE_SIZE,
    AgentStatus,
)

TEST_TOPIC = "test_topic"


async def wait_for_condition(condition_func, timeout=5.0, check_interval=0.1):
    """Wait for a condition to be true with timeout.

    Args:
        condition_func: Async function that returns bool
        timeout: Maximum time to wait in seconds
        check_interval: Time between checks in seconds

    Returns:
        bool: True if condition was met, False if timeout occurred
    """
    start_time = datetime.now()
    while (datetime.now() - start_time).total_seconds() < timeout:
        if await condition_func():
            return True
        await asyncio.sleep(check_interval)
    return False


class ProducerAgent(BaseAgent):
    """Test producer agent."""

    def __init__(self, agent_id: str, message_bus: Optional[MessageBus] = None):
        super().__init__(agent_type="producer", message_bus=message_bus)
        self.agent_id = agent_id  # Override UUID with provided ID
        self.messages_to_send = 5
        self.sent_count = 0

    async def start(self):
        """Start the agent and send a test message."""
        await self.initialize()
        message = Message.create(
            message_type=MessageType.EVENT,
            sender_id=self.agent_id,
            topic=TEST_TOPIC,
            payload={"test": "data"},
        )
        await self._message_bus.publish(message)

    async def _periodic_tasks(self):
        if self.sent_count < self.messages_to_send:
            message = Message.create(
                message_type=MessageType.EVENT,
                sender_id=self.agent_id,
                topic="test_topic",
                payload={"count": self.sent_count},
                priority=MessagePriority.NORMAL,
            )
            await self.send_message(message, topic="test_topic")
            self.sent_count += 1
            await asyncio.sleep(0.1)  # Small delay between messages


class ConsumerAgent(BaseAgent):
    """Test consumer agent."""

    def __init__(self, agent_id: str, message_bus: Optional[MessageBus] = None):
        super().__init__(agent_type="consumer", message_bus=message_bus)
        self.agent_id = agent_id  # Override UUID with provided ID
        self.received_message = None
        self.processed_count = 0

    async def start(self):
        """Start the agent."""
        await self.initialize()

    async def handle_message(self, message: Message):
        """Store received message."""
        self.received_message = message
        await self._handle_event(message)
        return await super().handle_message(message)

    async def _handle_event(self, message):
        await super()._handle_event(message)
        self.processed_count += 1


class ErrorAgent(BaseAgent):
    """Test agent that simulates an error."""

    def __init__(self, agent_id: str, message_bus: Optional[MessageBus] = None):
        super().__init__(agent_type="error", message_bus=message_bus)
        self.agent_id = agent_id  # Override UUID with provided ID

    async def start(self):
        """Start the agent."""
        await self.initialize()

    async def handle_message(self, message: Message):
        """Simulate an error on message handling."""
        self.status = AgentStatus.ERROR
        self.error_message = "Test error"
        raise ValueError("Test error")


@pytest.mark.asyncio
async def test_producer_consumer_flow():
    """Test basic producer-consumer message flow."""
    message_bus = MessageBus()
    await message_bus.initialize()

    # Create and initialize agents
    producer = ProducerAgent("producer", message_bus=message_bus)
    consumer = ConsumerAgent("consumer", message_bus=message_bus)

    # Initialize agents
    await producer.initialize()
    await consumer.initialize()

    # Subscribe consumer to test topic
    await consumer.subscribe_to_topic(TEST_TOPIC)

    # Start agents
    await producer.start()
    await consumer.start()

    # Wait for message processing
    await asyncio.sleep(0.1)

    # Verify message was received and processed
    assert consumer.received_message is not None
    assert consumer.received_message.payload == {"test": "data"}

    # Cleanup
    await producer.shutdown()
    await consumer.shutdown()
    await message_bus.shutdown()


@pytest.mark.asyncio
async def test_system_error_handling():
    """Test system-wide error handling and status updates."""
    message_bus = MessageBus()
    await message_bus.initialize()

    # Create and initialize agents
    producer = ProducerAgent("producer", message_bus=message_bus)
    error_agent = ErrorAgent("error_agent", message_bus=message_bus)

    # Initialize agents
    await producer.initialize()
    await error_agent.initialize()

    # Subscribe error agent to test topic
    await error_agent.subscribe_to_topic(TEST_TOPIC)

    # Start agents
    await producer.start()
    await error_agent.start()

    # Wait for error processing
    await asyncio.sleep(0.1)

    # Verify error status was updated
    assert error_agent.status == AgentStatus.ERROR
    assert error_agent.error_message == "Test error"

    # Cleanup
    await producer.shutdown()
    await error_agent.shutdown()
    await message_bus.shutdown()
