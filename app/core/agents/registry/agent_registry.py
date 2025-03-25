import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Type

from ..base.base_agent import BaseAgent
from ..protocols.agent_protocol import AgentStatus, AgentMetadata, AgentCapability


class AgentRegistry:
    """Central registry for managing all agents in the system"""

    def __init__(self, heartbeat_timeout: float = 90.0):
        self._agents: Dict[str, BaseAgent] = {}
        self._heartbeat_timeout = heartbeat_timeout
        self._cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """Initialize the registry"""
        try:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            return True
        except Exception:
            return False

    async def shutdown(self) -> bool:
        """Shutdown all agents and the registry"""
        try:
            # Cancel cleanup task
            if self._cleanup_task:
                self._cleanup_task.cancel()
                await asyncio.gather(self._cleanup_task, return_exceptions=True)

            # Shutdown all agents
            shutdown_tasks = [agent.shutdown() for agent in self._agents.values()]
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)

            self._agents.clear()
            return True
        except Exception:
            return False

    async def register_agent(self, agent: BaseAgent) -> bool:
        """Register a new agent"""
        try:
            if agent.agent_id in self._agents:
                return False

            await agent.initialize()
            self._agents[agent.agent_id] = agent
            return True
        except Exception:
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        try:
            if agent_id not in self._agents:
                return False

            agent = self._agents[agent_id]
            await agent.shutdown()
            del self._agents[agent_id]
            return True
        except Exception:
            return False

    async def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID"""
        return self._agents.get(agent_id)

    async def get_agents_by_type(self, agent_type: str) -> List[BaseAgent]:
        """Get all agents of a specific type"""
        return [
            agent for agent in self._agents.values() if agent.agent_type == agent_type
        ]

    async def get_agents_by_capability(self, capability_name: str) -> List[BaseAgent]:
        """Get all agents that have a specific capability"""
        return [
            agent
            for agent in self._agents.values()
            if any(cap.name == capability_name for cap in agent.capabilities)
        ]

    async def get_all_agents(self) -> List[BaseAgent]:
        """Get all registered agents"""
        return list(self._agents.values())

    async def get_agent_metadata(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get metadata for a specific agent"""
        agent = await self.get_agent(agent_id)
        if agent:
            return await agent.get_metadata()
        return None

    async def get_all_capabilities(self) -> List[AgentCapability]:
        """Get all available capabilities across all agents"""
        capabilities = set()
        for agent in self._agents.values():
            agent_capabilities = await agent.get_capabilities()
            for capability in agent_capabilities:
                capabilities.add(capability)
        return list(capabilities)

    async def _cleanup_loop(self, interval: float = 30.0):
        """Internal loop to cleanup inactive agents"""
        while True:
            try:
                await self._cleanup_inactive_agents()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception:
                continue

    async def _cleanup_inactive_agents(self):
        """Remove agents that haven't sent a heartbeat within the timeout period"""
        current_time = datetime.now()
        timeout_threshold = current_time - timedelta(seconds=self._heartbeat_timeout)

        inactive_agents = [
            agent_id
            for agent_id, agent in self._agents.items()
            if agent.last_heartbeat < timeout_threshold
        ]

        for agent_id in inactive_agents:
            await self.unregister_agent(agent_id)
