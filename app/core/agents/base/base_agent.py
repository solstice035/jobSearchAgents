import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..protocols.agent_protocol import (
    AgentProtocol,
    AgentStatus,
    AgentMetadata,
    AgentCapability,
)
from ..message_bus.message_types import Message, MessageType, MessagePriority
from ..message_bus.message_bus import MessageBus


class BaseAgent(AgentProtocol):
    """Base implementation of an agent with common functionality"""

    def __init__(self, agent_type: str, message_bus: MessageBus):
        self.agent_id = str(uuid.uuid4())
        self.agent_type = agent_type
        self.status = AgentStatus.INITIALIZING
        self.capabilities: List[AgentCapability] = []
        self.last_heartbeat = datetime.now()
        self.error_message: Optional[str] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._message_handler_task: Optional[asyncio.Task] = None
        self._message_bus = message_bus
        self._running = False

    async def initialize(self) -> bool:
        """Initialize the agent and start heartbeat"""
        try:
            # Register with message bus
            if not await self._message_bus.register_agent(self.agent_id):
                raise Exception("Failed to register with message bus")

            # Start message handler
            self._running = True
            self._message_handler_task = asyncio.create_task(
                self._message_handler_loop()
            )

            # Start heartbeat task
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            self.status = AgentStatus.READY
            return True
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.error_message = str(e)
            return False

    async def shutdown(self) -> bool:
        """Gracefully shutdown the agent"""
        try:
            self._running = False

            # Cancel message handler
            if self._message_handler_task:
                self._message_handler_task.cancel()
                await asyncio.gather(self._message_handler_task, return_exceptions=True)

            # Cancel heartbeat
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                await asyncio.gather(self._heartbeat_task, return_exceptions=True)

            # Unregister from message bus
            await self._message_bus.unregister_agent(self.agent_id)

            self.status = AgentStatus.SHUTDOWN
            return True
        except Exception as e:
            self.error_message = str(e)
            return False

    async def get_metadata(self) -> AgentMetadata:
        """Get current agent metadata"""
        return AgentMetadata(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=self.status,
            capabilities=self.capabilities,
            last_heartbeat=self.last_heartbeat,
            error_message=self.error_message,
        )

    async def update_status(
        self, status: AgentStatus, error_message: Optional[str] = None
    ) -> bool:
        """Update agent status"""
        try:
            self.status = status
            self.error_message = error_message

            # Broadcast status update
            message = Message.create(
                message_type=MessageType.STATUS,
                sender_id=self.agent_id,
                topic="agent.status",
                payload={"status": status.value, "error_message": error_message},
            )
            await self._message_bus.publish(message)
            return True
        except Exception:
            return False

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming messages - to be implemented by specific agents"""
        raise NotImplementedError("Specific agents must implement handle_message")

    async def heartbeat(self) -> datetime:
        """Send heartbeat"""
        self.last_heartbeat = datetime.now()

        # Send heartbeat message
        message = Message.create(
            message_type=MessageType.HEARTBEAT,
            sender_id=self.agent_id,
            topic="agent.heartbeat",
            payload={"timestamp": self.last_heartbeat.isoformat()},
        )
        await self._message_bus.publish(message)

        return self.last_heartbeat

    async def get_capabilities(self) -> List[AgentCapability]:
        """Get list of agent capabilities"""
        return self.capabilities

    async def _heartbeat_loop(self, interval: float = 30.0):
        """Internal heartbeat loop"""
        while self._running:
            try:
                await self.heartbeat()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.status = AgentStatus.ERROR
                self.error_message = f"Heartbeat error: {str(e)}"
                break

    async def _message_handler_loop(self):
        """Internal loop for handling incoming messages"""
        while self._running:
            try:
                message = await self._message_bus.get_message(
                    self.agent_id, timeout=1.0
                )
                if message:
                    response = await self.handle_message(message.payload)

                    # Send response if this was a query
                    if message.message_type == MessageType.QUERY and message.sender_id:
                        response_message = Message.create(
                            message_type=MessageType.RESPONSE,
                            sender_id=self.agent_id,
                            recipient_id=message.sender_id,
                            topic=f"response.{message.topic}",
                            payload=response,
                            correlation_id=message.message_id,
                        )
                        await self._message_bus.publish(response_message)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.status = AgentStatus.ERROR
                self.error_message = f"Message handler error: {str(e)}"
                continue

    def register_capability(self, capability: AgentCapability):
        """Register a new capability"""
        self.capabilities.append(capability)
