import pytest
from datetime import datetime, timedelta
import asyncio

from app.core.agents import Message, MessageType, MessagePriority
from app.tests.conftest import wait_for_message, wait_for_condition


@pytest.mark.asyncio
async def test_agent_registration(message_bus, test_agent):
    """Test agent registration and unregistration."""
    # Test registration
    assert test_agent.agent_id in message_bus.get_registered_agents()

    # Test unregistration
    await test_agent.stop()
    # Use wait_for_condition to ensure agent is fully unregistered
    assert await wait_for_condition(
        lambda: test_agent.agent_id not in message_bus.get_registered_agents()
    ), "Agent failed to unregister properly"


@pytest.mark.asyncio
async def test_topic_subscription(message_bus, test_agent):
    """Test topic subscription and unsubscription."""
    topic = "test_topic"

    # Test subscription
    await test_agent.subscribe_to_topic(topic)
    assert topic in test_agent.subscribed_topics
    assert test_agent.handle_message in message_bus.get_topic_subscribers(topic)

    # Verify subscription works by sending a test message
    test_message = Message.create(
        message_type=MessageType.EVENT,
        sender_id="test_sender",
        topic=topic,
        payload={"test": "subscription"},
        priority=MessagePriority.NORMAL,
    )
    await message_bus.publish(test_message)
    received = await wait_for_message(message_bus, test_agent.agent_id, topic=topic)
    assert received is not None, "Subscription test message not received"
    assert received.payload == test_message.payload

    # Test unsubscription
    await test_agent.unsubscribe_from_topic(topic)
    assert topic not in test_agent.subscribed_topics
    assert test_agent.handle_message not in message_bus.get_topic_subscribers(topic)

    # Verify unsubscription works
    await message_bus.publish(test_message)
    received = await wait_for_message(
        message_bus, test_agent.agent_id, topic=topic, timeout=0.5
    )
    assert received is None, "Message received after unsubscription"


@pytest.mark.asyncio
async def test_direct_messaging(message_bus, test_agent):
    """Test direct messaging between agents."""
    test_payload = {"action": "test", "data": "value"}
    message = Message.create(
        message_type=MessageType.COMMAND,
        sender_id="test_sender",
        topic="direct",
        payload=test_payload,
        recipient_id=test_agent.agent_id,
        priority=MessagePriority.NORMAL,
    )

    # Send direct message
    await message_bus.send_direct(message, test_agent.agent_id)

    # Use wait_for_message instead of get_next_message
    received = await wait_for_message(
        message_bus, test_agent.agent_id, message_type=MessageType.COMMAND
    )
    assert received is not None, "Message not received"
    assert str(received.message_id) == str(message.message_id)
    assert received.payload == test_payload, "Message payload does not match"
    assert received.sender_id == "test_sender"
    assert received.recipient_id == test_agent.agent_id

    await test_agent.handle_message(received)
    assert test_agent.command_count == 1
    assert len(test_agent.received_messages) == 1


@pytest.mark.asyncio
async def test_topic_publishing(message_bus, test_agent):
    """Test publishing messages to topics."""
    topic = "test_topic"
    await test_agent.subscribe_to_topic(topic)

    test_payload = {"event": "test", "timestamp": datetime.now().isoformat()}
    message = Message.create(
        message_type=MessageType.EVENT,
        sender_id="test_sender",
        topic=topic,
        payload=test_payload,
        priority=MessagePriority.LOW,
    )

    # Publish to topic
    await message_bus.publish(message)

    # Use wait_for_message for more reliable message receipt
    received = await wait_for_message(
        message_bus, test_agent.agent_id, message_type=MessageType.EVENT, topic=topic
    )
    assert received is not None, "Message not received"
    assert str(received.message_id) == str(message.message_id)
    assert received.payload == test_payload, "Message payload does not match"

    await test_agent.handle_message(received)
    assert test_agent.event_count == 1


@pytest.mark.asyncio
async def test_message_priority(message_bus, test_agent):
    """Test message priority handling."""
    messages = []
    priorities = [
        MessagePriority.URGENT,  # Highest priority first
        MessagePriority.HIGH,
        MessagePriority.NORMAL,
        MessagePriority.LOW,
    ]

    # Create and send messages with different priorities in reverse order
    for priority in reversed(priorities):
        message = Message.create(
            message_type=MessageType.COMMAND,
            sender_id="test_sender",
            topic="direct",
            payload={"priority": priority.name},
            recipient_id=test_agent.agent_id,
            priority=priority,
        )
        messages.append(message)
        await message_bus.send_direct(message, test_agent.agent_id)

    # Verify messages are received in priority order (highest to lowest)
    received_priorities = []
    for _ in range(len(priorities)):
        received = await wait_for_message(message_bus, test_agent.agent_id)
        assert received is not None, f"Message {_+1} not received"
        received_priorities.append(received.priority)

    assert received_priorities == priorities, "Messages not received in priority order"

    # Test FIFO order for same priority
    same_priority_msgs = []
    for i in range(3):
        message = Message.create(
            message_type=MessageType.COMMAND,
            sender_id="test_sender",
            topic="direct",
            payload={"sequence": i},
            recipient_id=test_agent.agent_id,
            priority=MessagePriority.NORMAL,
        )
        same_priority_msgs.append(message)
        await message_bus.send_direct(message, test_agent.agent_id)

    # Verify FIFO order
    received_sequence = []
    for _ in range(len(same_priority_msgs)):
        received = await wait_for_message(message_bus, test_agent.agent_id)
        assert received is not None, f"Same priority message {_+1} not received"
        received_sequence.append(received.payload["sequence"])

    assert received_sequence == [
        0,
        1,
        2,
    ], "Same priority messages not received in FIFO order"


@pytest.mark.asyncio
async def test_message_expiration(message_bus, test_agent):
    """Test message expiration handling."""
    # Use a fixed timestamp for all messages
    base_time = datetime(2025, 1, 1, 12, 0, 0)  # 2025-01-01 12:00:00
    check_time = datetime(2025, 1, 1, 12, 0, 1)  # 1 second after base_time

    # Create messages with different expiration times
    messages = [
        # Expired message
        Message.create(
            message_type=MessageType.COMMAND,
            sender_id="test_sender",
            topic="direct",
            payload={"test": "expired"},
            recipient_id=test_agent.agent_id,
            priority=MessagePriority.NORMAL,
            expires_at=base_time - timedelta(seconds=1),
        ),
        # Message expiring soon
        Message.create(
            message_type=MessageType.COMMAND,
            sender_id="test_sender",
            topic="direct",
            payload={"test": "expiring_soon"},
            recipient_id=test_agent.agent_id,
            priority=MessagePriority.NORMAL,
            expires_at=base_time + timedelta(seconds=2),  # Increased to 2 seconds
        ),
        # Valid message
        Message.create(
            message_type=MessageType.COMMAND,
            sender_id="test_sender",
            topic="direct",
            payload={"test": "valid"},
            recipient_id=test_agent.agent_id,
            priority=MessagePriority.NORMAL,
            expires_at=base_time + timedelta(minutes=5),
        ),
    ]

    # Print debug information
    print(f"\nCheck time: {check_time}")
    for i, msg in enumerate(messages):
        print(f"Message {i} expires at: {msg.expires_at}")
        print(f"Message {i} expired? {msg.is_expired(check_time)}")

    # Verify expiration times are set correctly
    assert messages[0].is_expired(check_time), "First message should be expired"
    assert not messages[1].is_expired(
        check_time
    ), "Second message should not be expired yet"
    assert not messages[2].is_expired(check_time), "Third message should not be expired"

    # Send all messages
    for message in messages:
        await message_bus.send_direct(
            message, test_agent.agent_id, check_time=check_time
        )

    # Wait briefly for message processing
    await asyncio.sleep(0.2)

    # Only the valid messages should be received
    received = await wait_for_message(
        message_bus, test_agent.agent_id, check_time=check_time
    )
    assert received is not None, "No message received"
    assert received.payload["test"] in [
        "expiring_soon",
        "valid",
    ], "Unexpected message received"

    # Get the second message if available
    second_received = await wait_for_message(
        message_bus, test_agent.agent_id, check_time=check_time
    )
    if second_received:
        assert second_received.payload["test"] == "valid", "Wrong message received"

    # No more messages should be available
    final_check = await wait_for_message(
        message_bus, test_agent.agent_id, timeout=0.1, check_time=check_time
    )
    assert final_check is None, "Unexpected additional message received"


@pytest.mark.asyncio
async def test_message_handling_errors(message_bus, test_agent):
    """Test error handling during message processing."""
    # Create a message that will cause an error
    error_message = Message.create(
        message_type=MessageType.COMMAND,
        sender_id="test_sender",
        topic="direct",
        payload=None,  # This should cause an error in message handling
        recipient_id=test_agent.agent_id,
        priority=MessagePriority.NORMAL,
    )

    # Send the message
    await message_bus.send_direct(error_message, test_agent.agent_id)

    # The message should still be received
    received = await wait_for_message(message_bus, test_agent.agent_id)
    assert received is not None, "Error-causing message not received"

    # Verify the message bus continues to function after error
    valid_message = Message.create(
        message_type=MessageType.COMMAND,
        sender_id="test_sender",
        topic="direct",
        payload={"test": "valid"},
        recipient_id=test_agent.agent_id,
        priority=MessagePriority.NORMAL,
    )

    await message_bus.send_direct(valid_message, test_agent.agent_id)
    received = await wait_for_message(message_bus, test_agent.agent_id)
    assert received is not None, "Valid message not received after error"
    assert received.payload == {"test": "valid"}
