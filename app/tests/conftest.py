"""Test configuration and fixtures."""

import asyncio
import pytest
from typing import AsyncGenerator, Generator, Dict, Any, Optional, Set
import logging
import tempfile
import os
from asyncio import TimeoutError
from datetime import datetime
import time

from app.core.agents import (
    BaseAgent,
    MessageBus,
    Message,
    setup_logging,
    get_monitor_manager,
)
from app.core.agents.message_bus import MessageType

CLEANUP_TIMEOUT = 5.0  # 5 second timeout for cleanup operations


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop

    try:
        # Clean up pending tasks with timeout
        pending = asyncio.all_tasks(loop)
        if pending:
            # Cancel all tasks to prevent hanging
            for task in pending:
                task.cancel()

            # Wait for tasks to complete with timeout
            try:
                loop.run_until_complete(
                    asyncio.wait_for(
                        asyncio.gather(*pending, return_exceptions=True),
                        timeout=CLEANUP_TIMEOUT,
                    )
                )
            except TimeoutError:
                logging.warning(
                    f"Timeout while cleaning up {len(pending)} pending tasks"
                )
            except Exception as e:
                logging.error(f"Error during task cleanup: {str(e)}")

        # Cleanup async generators
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
    finally:
        asyncio.set_event_loop(None)


@pytest.fixture
async def message_bus() -> AsyncGenerator[MessageBus, None]:
    """Create a message bus instance for testing."""
    bus = MessageBus()
    try:
        # Initialize the message bus
        if not await asyncio.wait_for(bus.initialize(), timeout=CLEANUP_TIMEOUT):
            raise RuntimeError("Failed to initialize message bus")
        yield bus
    finally:
        # Ensure cleanup happens even if test fails
        try:
            await asyncio.wait_for(bus.clear_all_queues(), timeout=CLEANUP_TIMEOUT)
            await asyncio.wait_for(bus.shutdown(), timeout=CLEANUP_TIMEOUT)
        except TimeoutError:
            logging.warning("Timeout while cleaning up message bus")
        except Exception as e:
            logging.error(f"Error during message bus cleanup: {str(e)}")


@pytest.fixture
def temp_log_dir() -> Generator[str, None, None]:
    """Create a temporary directory for test logs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Ensure the directory exists and is writable
        log_dir = os.path.join(temp_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        if not os.access(log_dir, os.W_OK):
            raise RuntimeError(f"Log directory {log_dir} is not writable")
        yield log_dir
        # Directory and contents will be cleaned up by context manager


@pytest.fixture
def configured_logging(temp_log_dir: str) -> Generator[None, None, None]:
    """Configure logging for tests with proper cleanup."""
    # Store original logging configuration
    original_handlers = logging.root.handlers.copy()

    try:
        # Configure test logging
        setup_logging(log_level="DEBUG", log_dir=temp_log_dir, console=True)
        yield
    finally:
        # Clean up logging configuration
        logging.root.handlers = original_handlers
        # Close any file handlers to ensure files are properly released
        for handler in logging.root.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()


@pytest.fixture
def monitor_manager():
    """Create a test monitor manager instance."""
    from app.core.agents.monitoring import MonitoringManager

    manager = MonitoringManager()
    try:
        yield manager
    finally:
        # Clean up any registered agents
        for agent_id in list(manager.get_active_agents()):
            manager.unregister_agent(agent_id)


class TestAgent(BaseAgent):
    """Base test agent class."""

    def __init__(self, agent_id: str, message_bus: Optional[MessageBus] = None):
        super().__init__(agent_type="test", message_bus=message_bus)
        self.agent_id = agent_id  # Override the UUID with the provided ID
        self._max_iterations = 100  # Prevent infinite loops in tests
        self._iteration_count = 0
        self._tasks: Set[asyncio.Task] = set()
        self.command_count = 0
        self.event_count = 0
        self.received_messages = []

    def _create_task(self, coro) -> asyncio.Task:
        """Create a task and track it for cleanup."""
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def _process_messages(self):
        """Override to add iteration limit for tests."""
        self._iteration_count += 1
        if self._iteration_count >= self._max_iterations:
            self._running = False
            self.logger.info("Maximum iterations reached in test environment")
            return
        await super()._process_messages()

    async def register_with_message_bus(self, message_bus: MessageBus) -> bool:
        """Register the agent with a message bus."""
        self._message_bus = message_bus
        return await self.initialize()

    async def start(self) -> None:
        """Start the agent's message processing loop."""
        await self.initialize()
        self._message_handler_task = self._create_task(self._message_handler_loop())

    async def stop(self) -> bool:
        """Stop the agent."""
        return await self.shutdown()

    async def _handle_command(self, message: Message) -> Dict[str, Any]:
        """Handle command messages for testing."""
        self.command_count += 1
        self.received_messages.append(message)
        return {"status": "success"}

    async def _handle_event(self, message: Message) -> Dict[str, Any]:
        """Handle event messages for testing."""
        self.event_count += 1
        self.received_messages.append(message)
        return {"status": "success"}

    async def _message_handler_loop(self):
        """Internal message processing loop."""
        while self._running:
            try:
                message = await self._message_bus.get_next_message(
                    self.agent_id, timeout=0.1
                )
                if message:
                    await self.handle_message(message)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break


@pytest.fixture
async def test_agent(message_bus: MessageBus) -> AsyncGenerator[TestAgent, None]:
    """Create a test agent instance."""
    agent = TestAgent("test_agent_1", message_bus)
    try:
        # Initialize the agent
        await asyncio.wait_for(
            agent.register_with_message_bus(message_bus), timeout=CLEANUP_TIMEOUT
        )
        await asyncio.wait_for(agent.start(), timeout=CLEANUP_TIMEOUT)
        yield agent
    finally:
        # Ensure cleanup happens even if test fails
        try:
            await asyncio.wait_for(agent.stop(), timeout=CLEANUP_TIMEOUT)
            # Wait for agent to fully stop
            await asyncio.wait_for(
                wait_for_condition(lambda: not agent.is_running),
                timeout=CLEANUP_TIMEOUT,
            )
        except TimeoutError:
            logging.warning("Timeout while stopping test agent")
        except Exception as e:
            logging.error(f"Error during test agent cleanup: {str(e)}")


async def wait_for_message(
    message_bus: MessageBus,
    agent_id: str,
    message_type: Optional[Any] = None,
    topic: Optional[str] = None,
    timeout: float = 1.0,
    check_time: Optional[datetime] = None,
) -> Optional[Message]:
    """Wait for a message to be received by the specified agent.

    Args:
        message_bus: The message bus instance
        agent_id: The agent ID to check messages for
        message_type: Optional MessageType to filter for
        topic: Optional topic to filter for
        timeout: How long to wait for a message in seconds
        check_time: Optional timestamp to use for expiration checks

    Returns:
        The received message or None if no message was received within the timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        # Get all messages
        messages = await message_bus.get_messages(agent_id, check_time=check_time)
        print(f"\nGot {len(messages)} messages from queue")
        if not messages:
            await asyncio.sleep(0.1)
            continue

        # Get the queue for putting back messages we don't want
        queue = message_bus._agent_queues[agent_id]

        # Clear the queue since get_messages returns all messages
        while not queue.empty():
            try:
                queue.get_nowait()
                queue.task_done()
            except asyncio.QueueEmpty:
                break

        # Find the first message that matches our criteria
        matching_message = None
        remaining_messages = []

        for message in messages:
            print(f"Checking message: {message.payload}")
            # For error test, accept messages with None payload
            if message.payload is None and message_type == MessageType.COMMAND:
                print("Found error message with None payload")
                matching_message = message
                remaining_messages.extend(messages[messages.index(message) + 1 :])
                break

            # Check if message matches our filters
            if message_type is not None and message.message_type != message_type:
                print(
                    f"Message type {message.message_type} doesn't match {message_type}"
                )
                remaining_messages.append(message)
                continue
            if topic is not None and message.topic != topic:
                print(f"Topic {message.topic} doesn't match {topic}")
                remaining_messages.append(message)
                continue

            # Found a matching message
            print(f"Found matching message: {message.payload}")
            matching_message = message
            remaining_messages.extend(messages[messages.index(message) + 1 :])
            break

        # If no matching message was found, all messages go back in the queue
        if matching_message is None:
            print("No matching message found, putting all messages back")
            remaining_messages = messages

        # Put remaining messages back in the queue in the original order
        for message in remaining_messages:
            print(f"Putting back message: {message.payload}")
            await queue.put(message)

        if matching_message:
            return matching_message

        await asyncio.sleep(0.1)

    return None


async def wait_for_condition(
    condition_func: Any, timeout: float = 1.0, check_interval: float = 0.1
) -> bool:
    """Wait for a condition to be true with timeout.

    Args:
        condition_func: Function that returns bool (can be sync or async)
        timeout: Maximum time to wait in seconds
        check_interval: How often to check the condition

    Returns:
        bool: True if condition met, False if timeout reached
    """
    try:
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                # Handle both sync and async functions
                if asyncio.iscoroutinefunction(condition_func):
                    result = await condition_func()
                else:
                    result = condition_func()

                if result:
                    return True
            except Exception as e:
                logging.warning(f"Error checking condition: {str(e)}")
            await asyncio.sleep(check_interval)
        return False
    except Exception as e:
        logging.error(f"Error in wait_for_condition: {str(e)}")
        return False
