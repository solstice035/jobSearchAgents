import pytest
from datetime import datetime, timedelta

from app.core.agents import Message, MessageType, MessagePriority


@pytest.mark.asyncio
async def test_agent_registration(message_bus, test_agent):
    """Test agent registration and unregistration."""
    # Test registration
    assert test_agent.agent_id in message_bus.get_registered_agents()

    # Test unregistration
    await test_agent.stop()
    assert test_agent.agent_id not in message_bus.get_registered_agents()


@pytest.mark.asyncio
async def test_topic_subscription(message_bus, test_agent):
    """Test topic subscription and unsubscription."""
    topic = "test_topic"

    # Test subscription
    test_agent.subscribe_to_topic(topic)
    assert topic in test_agent.subscribed_topics
    assert test_agent.agent_id in message_bus.get_topic_subscribers(topic)

    # Test unsubscription
    test_agent.unsubscribe_from_topic(topic)
    assert topic not in test_agent.subscribed_topics
    assert test_agent.agent_id not in message_bus.get_topic_subscribers(topic)


@pytest.mark.asyncio
async def test_direct_messaging(message_bus, test_agent):
    """Test direct messaging between agents."""
    message = Message(
        id="test_msg_1",
        type=MessageType.COMMAND,
        content={"action": "test"},
        priority=MessagePriority.NORMAL,
    )

    # Send direct message
    await message_bus.send_direct(message, test_agent.agent_id)

    # Get and process message
    received = await message_bus.get_next_message(test_agent.agent_id)
    assert received is not None
    assert received.id == message.id

    await test_agent.handle_message(received)
    assert test_agent.command_count == 1
    assert len(test_agent.received_messages) == 1


@pytest.mark.asyncio
async def test_topic_publishing(message_bus, test_agent):
    """Test publishing messages to topics."""
    topic = "test_topic"
    test_agent.subscribe_to_topic(topic)

    message = Message(
        id="test_msg_2",
        type=MessageType.EVENT,
        content={"event": "test"},
        priority=MessagePriority.LOW,
    )

    # Publish to topic
    await message_bus.publish(message, topic)

    # Get and process message
    received = await message_bus.get_next_message(test_agent.agent_id)
    assert received is not None
    assert received.id == message.id

    await test_agent.handle_message(received)
    assert test_agent.event_count == 1


@pytest.mark.asyncio
async def test_message_priority(message_bus, test_agent):
    """Test message priority handling."""
    # Send messages with different priorities
    low_priority = Message(
        id="low",
        type=MessageType.COMMAND,
        content={"priority": "low"},
        priority=MessagePriority.LOW,
    )

    high_priority = Message(
        id="high",
        type=MessageType.COMMAND,
        content={"priority": "high"},
        priority=MessagePriority.HIGH,
    )

    # Send low priority first
    await message_bus.send_direct(low_priority, test_agent.agent_id)
    await message_bus.send_direct(high_priority, test_agent.agent_id)

    # High priority should be received first
    first_msg = await message_bus.get_next_message(test_agent.agent_id)
    assert first_msg.id == "high"

    second_msg = await message_bus.get_next_message(test_agent.agent_id)
    assert second_msg.id == "low"


@pytest.mark.asyncio
async def test_message_expiration(message_bus, test_agent):
    """Test message expiration handling."""
    # Create expired message
    expired_message = Message(
        id="expired",
        type=MessageType.COMMAND,
        content={"test": "expired"},
        priority=MessagePriority.NORMAL,
        expiration=datetime.now() - timedelta(seconds=1),
    )

    # Create valid message
    valid_message = Message(
        id="valid",
        type=MessageType.COMMAND,
        content={"test": "valid"},
        priority=MessagePriority.NORMAL,
        expiration=datetime.now() + timedelta(minutes=5),
    )

    # Send both messages
    await message_bus.send_direct(expired_message, test_agent.agent_id)
    await message_bus.send_direct(valid_message, test_agent.agent_id)

    # Only valid message should be received
    msg = await message_bus.get_next_message(test_agent.agent_id)
    assert msg is not None
    assert msg.id == "valid"

    # No more messages should be available
    msg = await message_bus.get_next_message(test_agent.agent_id)
    assert msg is None
