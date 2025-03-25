import asyncio
import pytest
from typing import AsyncGenerator, Generator

import logging
import tempfile
import os

from app.core.agents import BaseAgent, MessageBus, setup_logging, get_monitor_manager


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def message_bus() -> AsyncGenerator[MessageBus, None]:
    """Create a message bus instance for testing."""
    bus = MessageBus()
    await bus.initialize()
    yield bus
    # Cleanup
    await bus.shutdown()


@pytest.fixture
def temp_log_dir() -> Generator[str, None, None]:
    """Create a temporary directory for test logs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def configured_logging(temp_log_dir: str) -> None:
    """Configure logging for tests."""
    setup_logging(log_level="DEBUG", log_dir=temp_log_dir, console=True)


@pytest.fixture
def monitor_manager():
    """Get the monitor manager instance and ensure it's clean."""
    manager = get_monitor_manager()
    yield manager
    # Cleanup
    for agent_id in list(manager.get_active_agents()):
        manager.unregister_agent(agent_id)


class TestAgent(BaseAgent):
    """A simple agent implementation for testing."""

    def __init__(self, agent_id: str, agent_type: str = "test_agent"):
        super().__init__(agent_id, agent_type)
        self.received_messages = []
        self.command_count = 0
        self.query_count = 0
        self.event_count = 0

    async def _handle_command(self, message):
        self.command_count += 1
        self.received_messages.append(message)

    async def _handle_query(self, message):
        self.query_count += 1
        self.received_messages.append(message)

    async def _handle_event(self, message):
        self.event_count += 1
        self.received_messages.append(message)


@pytest.fixture
async def test_agent(message_bus: MessageBus) -> AsyncGenerator[TestAgent, None]:
    """Create a test agent instance."""
    agent = TestAgent("test_agent_1")
    await agent.register_with_message_bus(message_bus)
    yield agent
    # Cleanup
    await agent.stop()
