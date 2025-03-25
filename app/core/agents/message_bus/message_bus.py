import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Dict, Set, List, Optional, Callable, Awaitable, Any
from uuid import UUID

from .message_types import Message, MessagePriority

MessageHandler = Callable[[Message], Awaitable[None]]


class MessageBus:
    """Central message bus for agent communication"""

    def __init__(self, max_queue_size: int = 1000):
        self._subscribers: Dict[str, Set[MessageHandler]] = defaultdict(set)
        self._agent_queues: Dict[str, asyncio.Queue[Message]] = {}
        self._max_queue_size = max_queue_size
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """Initialize the message bus"""
        try:
            self._running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            return True
        except Exception:
            return False

    async def shutdown(self) -> bool:
        """Shutdown the message bus"""
        try:
            self._running = False
            if self._cleanup_task:
                self._cleanup_task.cancel()
                await asyncio.gather(self._cleanup_task, return_exceptions=True)

            # Clear all queues
            for queue in self._agent_queues.values():
                while not queue.empty():
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

            self._agent_queues.clear()
            self._subscribers.clear()
            return True
        except Exception:
            return False

    async def register_agent(self, agent_id: str) -> bool:
        """Register an agent to receive messages"""
        try:
            if agent_id not in self._agent_queues:
                self._agent_queues[agent_id] = asyncio.Queue(
                    maxsize=self._max_queue_size
                )
            return True
        except Exception:
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        try:
            if agent_id in self._agent_queues:
                del self._agent_queues[agent_id]
            return True
        except Exception:
            return False

    async def subscribe(self, topic: str, handler: MessageHandler) -> bool:
        """Subscribe to messages on a specific topic"""
        try:
            self._subscribers[topic].add(handler)
            return True
        except Exception:
            return False

    async def unsubscribe(self, topic: str, handler: MessageHandler) -> bool:
        """Unsubscribe from a topic"""
        try:
            if topic in self._subscribers:
                self._subscribers[topic].discard(handler)
                if not self._subscribers[topic]:
                    del self._subscribers[topic]
            return True
        except Exception:
            return False

    async def publish(self, message: Message) -> bool:
        """Publish a message to subscribers and/or specific recipient"""
        try:
            # Handle broadcast messages
            if message.is_broadcast():
                await self._handle_broadcast(message)
            # Handle directed messages
            elif message.recipient_id:
                await self._handle_directed_message(message)
            return True
        except Exception:
            return False

    async def get_message(
        self, agent_id: str, timeout: Optional[float] = None
    ) -> Optional[Message]:
        """Get next message for an agent"""
        try:
            if agent_id not in self._agent_queues:
                return None

            queue = self._agent_queues[agent_id]
            try:
                message = await asyncio.wait_for(queue.get(), timeout=timeout)
                queue.task_done()
                return message
            except asyncio.TimeoutError:
                return None
        except Exception:
            return None

    async def _handle_broadcast(self, message: Message):
        """Handle broadcast message delivery"""
        handlers = self._subscribers.get(message.topic, set())

        # Create tasks for all handlers
        tasks = [asyncio.create_task(handler(message)) for handler in handlers]

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _handle_directed_message(self, message: Message):
        """Handle directed message delivery"""
        if message.recipient_id in self._agent_queues:
            queue = self._agent_queues[message.recipient_id]
            try:
                await queue.put(message)
            except asyncio.QueueFull:
                # If queue is full, remove oldest low priority message
                await self._make_space_in_queue(queue)
                await queue.put(message)

    async def _make_space_in_queue(self, queue: asyncio.Queue[Message]):
        """Remove oldest low priority message to make space"""
        messages: List[Message] = []

        # Empty the queue
        while not queue.empty():
            try:
                msg = queue.get_nowait()
                messages.append(msg)
                queue.task_done()
            except asyncio.QueueEmpty:
                break

        # Sort by priority and timestamp
        messages.sort(key=lambda m: (m.priority.value, m.timestamp), reverse=True)

        # Put back all but the oldest low priority message
        for msg in messages[:-1]:
            await queue.put(msg)

    async def _cleanup_loop(self, interval: float = 60.0):
        """Periodically clean up expired messages"""
        while self._running:
            try:
                await self._cleanup_expired_messages()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception:
                continue

    async def _cleanup_expired_messages(self):
        """Remove expired messages from all queues"""
        for queue in self._agent_queues.values():
            messages: List[Message] = []

            # Empty the queue
            while not queue.empty():
                try:
                    msg = queue.get_nowait()
                    if not msg.is_expired():
                        messages.append(msg)
                    queue.task_done()
                except asyncio.QueueEmpty:
                    break

            # Put back unexpired messages
            for msg in messages:
                await queue.put(msg)
