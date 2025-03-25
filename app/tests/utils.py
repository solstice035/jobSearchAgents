"""Utility functions for testing."""

import asyncio
from typing import Callable, Any, Optional
from app.core.agents import Message, MessageType


async def wait_for_condition(
    condition: Callable[[], bool], timeout: float = 1.0, interval: float = 0.1
) -> bool:
    """
    Wait for a condition to be true.

    Args:
        condition: Function that returns a boolean
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds

    Returns:
        bool: True if condition was met, False if timeout occurred
    """
    end_time = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < end_time:
        if condition():
            return True
        await asyncio.sleep(interval)
    return False


async def wait_for_message(
    message_bus: Any,
    recipient_id: str,
    message_type: Optional[MessageType] = None,
    timeout: float = 1.0,
) -> Optional[Message]:
    """
    Wait for a message to be received by a specific recipient.

    Args:
        message_bus: The message bus instance
        recipient_id: ID of the recipient to wait for
        message_type: Optional message type to filter for
        timeout: Maximum time to wait in seconds

    Returns:
        Message or None: The received message or None if timeout occurred
    """

    async def check_message():
        messages = await message_bus.get_messages(recipient_id)
        if not messages:
            return None
        if message_type:
            messages = [m for m in messages if m.message_type == message_type]
        return messages[0] if messages else None

    end_time = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < end_time:
        message = await check_message()
        if message:
            return message
        await asyncio.sleep(0.1)
    return None
