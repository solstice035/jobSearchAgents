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
    await test_agent.subscribe_to_topic(topic)
    assert topic in test_agent.subscribed_topics
    assert test_agent.handle_message in message_bus.get_topic_subscribers(topic)

    # Test unsubscription
    await test_agent.unsubscribe_from_topic(topic)
    assert topic not in test_agent.subscribed_topics
    assert test_agent.handle_message not in message_bus.get_topic_subscribers(topic)


@pytest.mark.asyncio
async def test_direct_messaging(message_bus, test_agent):
    """Test direct messaging between agents."""
    message = Message.create(
        message_type=MessageType.COMMAND,
        sender_id="test_sender",
        topic="direct",
        payload={"action": "test"},
        recipient_id=test_agent.agent_id,
        priority=MessagePriority.NORMAL,
    )

    # Send direct message
    await message_bus.send_direct(message, test_agent.agent_id)

    # Get and process message
    received = await message_bus.get_next_message(test_agent.agent_id)
    assert received is not None
    assert str(received.message_id) == str(message.message_id)

    await test_agent.handle_message(received)
    assert test_agent.command_count == 1
    assert len(test_agent.received_messages) == 1


@pytest.mark.asyncio
async def test_topic_publishing(message_bus, test_agent):
    """Test publishing messages to topics."""
    topic = "test_topic"
    await test_agent.subscribe_to_topic(topic)

    message = Message.create(
        message_type=MessageType.EVENT,
        sender_id="test_sender",
        topic=topic,
        payload={"event": "test"},
        priority=MessagePriority.LOW,
    )

    # Publish to topic
    await message_bus.publish(message)

    # Get and process message
    received = await message_bus.get_next_message(test_agent.agent_id)
    assert received is not None
    assert str(received.message_id) == str(message.message_id)

    await test_agent.handle_message(received)
    assert test_agent.event_count == 1


@pytest.mark.asyncio
async def test_message_priority(message_bus, test_agent):
    """Test message priority handling."""
    # Send messages with different priorities
    low_priority = Message.create(
        message_type=MessageType.COMMAND,
        sender_id="test_sender",
        topic="direct",
        payload={"priority": "low"},
        recipient_id=test_agent.agent_id,
        priority=MessagePriority.LOW,
    )

    high_priority = Message.create(
        message_type=MessageType.COMMAND,
        sender_id="test_sender",
        topic="direct",
        payload={"priority": "high"},
        recipient_id=test_agent.agent_id,
        priority=MessagePriority.HIGH,
    )

    # Send low priority first
    await message_bus.send_direct(low_priority, test_agent.agent_id)
    await message_bus.send_direct(high_priority, test_agent.agent_id)

    # High priority should be received first
    first_msg = await message_bus.get_next_message(test_agent.agent_id)
    assert str(first_msg.message_id) == str(high_priority.message_id)

    second_msg = await message_bus.get_next_message(test_agent.agent_id)
    assert str(second_msg.message_id) == str(low_priority.message_id)


@pytest.mark.asyncio
async def test_message_expiration(message_bus, test_agent):
    """Test message expiration handling."""
    # Create expired message
    expired_message = Message.create(
        message_type=MessageType.COMMAND,
        sender_id="test_sender",
        topic="direct",
        payload={"test": "expired"},
        recipient_id=test_agent.agent_id,
        priority=MessagePriority.NORMAL,
        expires_at=datetime.now() - timedelta(seconds=1),
    )

    # Create valid message
    valid_message = Message.create(
        message_type=MessageType.COMMAND,
        sender_id="test_sender",
        topic="direct",
        payload={"test": "valid"},
        recipient_id=test_agent.agent_id,
        priority=MessagePriority.NORMAL,
        expires_at=datetime.now() + timedelta(minutes=5),
    )

    # Send both messages
    await message_bus.send_direct(expired_message, test_agent.agent_id)
    await message_bus.send_direct(valid_message, test_agent.agent_id)

    # Only valid message should be received
    msg = await message_bus.get_next_message(test_agent.agent_id)
    assert msg is not None
    assert str(msg.message_id) == str(valid_message.message_id)

    # No more messages should be available
    msg = await message_bus.get_next_message(test_agent.agent_id)
    assert msg is None
