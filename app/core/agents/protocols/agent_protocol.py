from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List


class AgentStatus(Enum):
    """Enum representing possible agent states"""

    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class AgentCapability:
    """Represents a specific capability an agent can perform"""

    name: str
    description: str
    parameters: Dict[str, Any]
    required_resources: List[str]


@dataclass
class AgentMetadata:
    """Metadata about an agent instance"""

    agent_id: str
    agent_type: str
    status: AgentStatus
    capabilities: List[AgentCapability]
    last_heartbeat: datetime
    error_message: Optional[str] = None


class AgentProtocol(ABC):
    """Base protocol that all agents must implement"""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the agent and its resources"""
        pass

    @abstractmethod
    async def shutdown(self) -> bool:
        """Gracefully shutdown the agent"""
        pass

    @abstractmethod
    async def get_metadata(self) -> AgentMetadata:
        """Get current agent metadata"""
        pass

    @abstractmethod
    async def update_status(
        self, status: AgentStatus, error_message: Optional[str] = None
    ) -> bool:
        """Update agent status"""
        pass

    @abstractmethod
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming messages"""
        pass

    @abstractmethod
    async def heartbeat(self) -> datetime:
        """Send heartbeat to indicate agent is alive"""
        pass

    @abstractmethod
    async def get_capabilities(self) -> List[AgentCapability]:
        """Get list of agent capabilities"""
        pass
