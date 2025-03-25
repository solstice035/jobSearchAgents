from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from uuid import UUID, uuid4


class MessageType(Enum):
    """Types of messages that can be sent between agents"""

    COMMAND = "command"  # Direct command to an agent
    EVENT = "event"  # Broadcast event notification
    QUERY = "query"  # Request for information
    RESPONSE = "response"  # Response to a query
    ERROR = "error"  # Error notification
    STATUS = "status"  # Status update
    HEARTBEAT = "heartbeat"  # Agent heartbeat


class MessagePriority(Enum):
    """Priority levels for messages"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class Message:
    """Base message structure for agent communication"""

    message_id: UUID
    message_type: MessageType
    sender_id: str
    recipient_id: Optional[str]  # None for broadcast messages
    topic: str
    payload: Dict[str, Any]
    priority: MessagePriority
    timestamp: datetime
    correlation_id: Optional[UUID] = None  # For linking related messages
    expires_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        message_type: MessageType,
        sender_id: str,
        topic: str,
        payload: Dict[str, Any],
        recipient_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: Optional[UUID] = None,
        expires_at: Optional[datetime] = None,
    ) -> "Message":
        """Factory method to create a new message"""
        now = datetime.now()
        return cls(
            message_id=uuid4(),
            message_type=message_type,
            sender_id=sender_id,
            recipient_id=recipient_id,
            topic=topic,
            payload=payload,
            priority=priority,
            timestamp=now,
            correlation_id=correlation_id,
            expires_at=expires_at,
        )

    def is_expired(self, current_time: Optional[datetime] = None) -> bool:
        """Check if message has expired"""
        if self.expires_at is None:
            return False
        if current_time is None:
            current_time = datetime.now()
        return current_time > self.expires_at

    def is_broadcast(self) -> bool:
        """Check if message is a broadcast message"""
        return self.recipient_id is None
