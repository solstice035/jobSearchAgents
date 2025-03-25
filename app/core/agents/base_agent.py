import asyncio
import time
from typing import Any, Dict, Optional, Set, Type

from .message_bus import Message, MessageBus, MessageType
from .monitoring import (
    AgentLogger,
    AgentMetrics,
    DEFAULT_METRICS,
    get_monitor_manager,
    MESSAGES_PROCESSED,
    MESSAGES_SENT,
    PROCESSING_TIME,
    QUEUE_SIZE,
    AGENT_STATUS,
)


class BaseAgent:
    """Base class for all agents in the system"""

    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.message_bus: Optional[MessageBus] = None
        self.subscribed_topics: Set[str] = set()
        self._running = False

        # Setup logging
        self.logger = AgentLogger(agent_id, agent_type)

        # Setup monitoring
        self.metrics = get_monitor_manager().register_agent(agent_id)
        self._setup_default_metrics()

        self.logger.info(
            "Agent initialized",
            {
                "agent_type": agent_type,
                "subscribed_topics": list(self.subscribed_topics),
            },
        )

    def _setup_default_metrics(self):
        """Setup default metrics for the agent"""
        for metric_name, metric_type in DEFAULT_METRICS.items():
            self.metrics.register_metric(metric_name, metric_type)

        # Set initial status
        self.metrics.record_value(AGENT_STATUS, 0)  # 0 = initialized

    def register_with_message_bus(self, message_bus: MessageBus) -> None:
        """Register the agent with a message bus"""
        self.message_bus = message_bus
        self.message_bus.register_agent(self)
        self.logger.info("Registered with message bus")

    def subscribe_to_topic(self, topic: str) -> None:
        """Subscribe to a topic"""
        if self.message_bus:
            self.message_bus.subscribe(self, topic)
            self.subscribed_topics.add(topic)
            self.logger.info(f"Subscribed to topic: {topic}")

    def unsubscribe_from_topic(self, topic: str) -> None:
        """Unsubscribe from a topic"""
        if self.message_bus and topic in self.subscribed_topics:
            self.message_bus.unsubscribe(self, topic)
            self.subscribed_topics.remove(topic)
            self.logger.info(f"Unsubscribed from topic: {topic}")

    async def start(self) -> None:
        """Start the agent"""
        self._running = True
        self.metrics.record_value(AGENT_STATUS, 1)  # 1 = running
        self.logger.info("Agent started")

        try:
            await self._run()
        except Exception as e:
            self.logger.error(
                f"Agent crashed: {str(e)}",
                {"error_type": type(e).__name__, "error_details": str(e)},
            )
            self.metrics.record_value(AGENT_STATUS, -1)  # -1 = error
            raise

    async def stop(self) -> None:
        """Stop the agent"""
        self._running = False
        self.metrics.record_value(AGENT_STATUS, 2)  # 2 = stopped
        self.logger.info("Agent stopped")

        if self.message_bus:
            self.message_bus.unregister_agent(self)
            get_monitor_manager().unregister_agent(self.agent_id)

    async def handle_message(self, message: Message) -> None:
        """Handle an incoming message"""
        start_time = time.time()

        try:
            # Update metrics before processing
            self.metrics.record_value(MESSAGES_PROCESSED, 1)
            queue_size = len(self.message_bus.get_agent_queue(self.agent_id))
            self.metrics.record_value(QUEUE_SIZE, queue_size)

            # Process message based on type
            if message.type == MessageType.COMMAND:
                await self._handle_command(message)
            elif message.type == MessageType.QUERY:
                await self._handle_query(message)
            elif message.type == MessageType.EVENT:
                await self._handle_event(message)

            # Record processing time
            processing_time = time.time() - start_time
            self.metrics.record_value(PROCESSING_TIME, processing_time)

            self.logger.debug(
                f"Processed message",
                {
                    "message_id": message.id,
                    "message_type": message.type.name,
                    "processing_time": processing_time,
                },
            )

        except Exception as e:
            self.logger.error(
                f"Error processing message: {str(e)}",
                {
                    "message_id": message.id,
                    "message_type": message.type.name,
                    "error_type": type(e).__name__,
                    "error_details": str(e),
                },
            )
            raise

    async def send_message(
        self,
        message: Message,
        topic: Optional[str] = None,
        target_agent: Optional[str] = None,
    ) -> None:
        """Send a message"""
        if not self.message_bus:
            raise RuntimeError("Agent not registered with message bus")

        if topic:
            await self.message_bus.publish(message, topic)
        elif target_agent:
            await self.message_bus.send_direct(message, target_agent)
        else:
            raise ValueError("Must specify either topic or target_agent")

        self.metrics.record_value(MESSAGES_SENT, 1)
        self.logger.debug(
            f"Sent message",
            {
                "message_id": message.id,
                "message_type": message.type.name,
                "topic": topic,
                "target_agent": target_agent,
            },
        )

    async def _run(self) -> None:
        """Main agent loop"""
        self.logger.info("Agent run loop started")

        while self._running:
            try:
                # Process messages from queue
                if self.message_bus:
                    message = await self.message_bus.get_next_message(self.agent_id)
                    if message:
                        await self.handle_message(message)

                # Allow for agent-specific periodic tasks
                await self._periodic_tasks()

            except Exception as e:
                self.logger.error(
                    f"Error in run loop: {str(e)}",
                    {"error_type": type(e).__name__, "error_details": str(e)},
                )
                await asyncio.sleep(1)  # Prevent tight error loop

    async def _periodic_tasks(self) -> None:
        """Override to implement agent-specific periodic tasks"""
        pass

    async def _handle_command(self, message: Message) -> None:
        """Override to implement command handling"""
        pass

    async def _handle_query(self, message: Message) -> None:
        """Override to implement query handling"""
        pass

    async def _handle_event(self, message: Message) -> None:
        """Override to implement event handling"""
        pass
