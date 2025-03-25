import asyncio
import pytest
from datetime import datetime, timedelta

from app.core.agents import (
    Message,
    MessageType,
    MessagePriority,
    MESSAGES_PROCESSED,
    MESSAGES_SENT,
    PROCESSING_TIME,
    QUEUE_SIZE,
)


class ProducerAgent(TestAgent):
    """Agent that produces messages."""

    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.messages_to_send = 5
        self.sent_count = 0

    async def _periodic_tasks(self):
        if self.sent_count < self.messages_to_send:
            message = Message(
                id=f"msg_{self.sent_count}",
                type=MessageType.EVENT,
                content={"count": self.sent_count},
                priority=MessagePriority.NORMAL,
            )
            await self.send_message(message, topic="test_topic")
            self.sent_count += 1
            await asyncio.sleep(0.1)  # Small delay between messages


class ConsumerAgent(TestAgent):
    """Agent that consumes messages."""

    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.processed_count = 0

    async def _handle_event(self, message):
        await super()._handle_event(message)
        self.processed_count += 1


@pytest.mark.asyncio
async def test_producer_consumer_flow(message_bus, monitor_manager, configured_logging):
    """Test complete flow with producer and consumer agents."""
    # Create and setup agents
    producer = ProducerAgent("producer_1")
    consumer = ConsumerAgent("consumer_1")

    producer.register_with_message_bus(message_bus)
    consumer.register_with_message_bus(message_bus)
    consumer.subscribe_to_topic("test_topic")

    # Start agents
    producer_task = asyncio.create_task(producer.start())
    consumer_task = asyncio.create_task(consumer.start())

    # Wait for processing to complete
    await asyncio.sleep(1)  # Allow time for message processing

    # Stop agents
    await producer.stop()
    await consumer.stop()

    # Cancel tasks
    producer_task.cancel()
    consumer_task.cancel()
    try:
        await producer_task
    except asyncio.CancelledError:
        pass
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    # Verify message flow
    assert producer.sent_count == producer.messages_to_send
    assert consumer.processed_count == producer.messages_to_send

    # Verify metrics
    producer_metrics = monitor_manager.get_agent_metrics(producer.agent_id)
    consumer_metrics = monitor_manager.get_agent_metrics(consumer.agent_id)

    # Producer metrics
    sent_values = producer_metrics.get_metric(MESSAGES_SENT).get_values()
    assert len(sent_values) == producer.messages_to_send

    # Consumer metrics
    processed_values = consumer_metrics.get_metric(MESSAGES_PROCESSED).get_values()
    assert len(processed_values) == producer.messages_to_send

    # Verify processing times were recorded
    processing_times = consumer_metrics.get_metric(PROCESSING_TIME).get_values()
    assert len(processing_times) == producer.messages_to_send

    # Verify queue sizes were monitored
    queue_sizes = consumer_metrics.get_metric(QUEUE_SIZE).get_values()
    assert len(queue_sizes) > 0


@pytest.mark.asyncio
async def test_system_error_handling(message_bus, monitor_manager, configured_logging):
    """Test system behavior with error conditions."""

    class ErrorAgent(TestAgent):
        def __init__(self, agent_id: str):
            super().__init__(agent_id)
            self.error_on_message = 3  # Fail on 3rd message

        async def _handle_event(self, message):
            if len(self.received_messages) + 1 == self.error_on_message:
                raise ValueError("Simulated error")
            await super()._handle_event(message)

    # Setup agents
    producer = ProducerAgent("producer_2")
    error_agent = ErrorAgent("error_agent")

    producer.register_with_message_bus(message_bus)
    error_agent.register_with_message_bus(message_bus)
    error_agent.subscribe_to_topic("test_topic")

    # Start agents
    producer_task = asyncio.create_task(producer.start())
    error_agent_task = asyncio.create_task(error_agent.start())

    # Wait for processing
    await asyncio.sleep(1)

    # Stop agents
    await producer.stop()
    await error_agent.stop()

    # Cancel tasks
    producer_task.cancel()
    error_agent_task.cancel()
    try:
        await producer_task
    except asyncio.CancelledError:
        pass
    try:
        await error_agent_task
    except asyncio.CancelledError:
        pass

    # Verify error handling
    assert (
        len(error_agent.received_messages) == 2
    )  # Should have processed 2 messages before error

    # Check metrics
    error_metrics = monitor_manager.get_agent_metrics(error_agent.agent_id)
    processed = error_metrics.get_metric(MESSAGES_PROCESSED).get_values()
    assert len(processed) == 2  # Should have recorded 2 successful processes

    # Verify agent status indicates error
    status = error_metrics.get_metric("agent_status").get_values()[-1]
    assert status.value == -1  # Error status
