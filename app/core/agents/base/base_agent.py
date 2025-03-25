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


class BaseAgent(AgentProtocol):
    """Base implementation of an agent with common functionality"""

    def __init__(self, agent_type: str):
        self.agent_id = str(uuid.uuid4())
        self.agent_type = agent_type
        self.status = AgentStatus.INITIALIZING
        self.capabilities: List[AgentCapability] = []
        self.last_heartbeat = datetime.now()
        self.error_message: Optional[str] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """Initialize the agent and start heartbeat"""
        try:
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
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                await asyncio.gather(self._heartbeat_task, return_exceptions=True)
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
            return True
        except Exception:
            return False

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming messages - to be implemented by specific agents"""
        raise NotImplementedError("Specific agents must implement handle_message")

    async def heartbeat(self) -> datetime:
        """Send heartbeat"""
        self.last_heartbeat = datetime.now()
        return self.last_heartbeat

    async def get_capabilities(self) -> List[AgentCapability]:
        """Get list of agent capabilities"""
        return self.capabilities

    async def _heartbeat_loop(self, interval: float = 30.0):
        """Internal heartbeat loop"""
        while True:
            try:
                await self.heartbeat()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.status = AgentStatus.ERROR
                self.error_message = f"Heartbeat error: {str(e)}"
                break

    def register_capability(self, capability: AgentCapability):
        """Register a new capability"""
        self.capabilities.append(capability)
