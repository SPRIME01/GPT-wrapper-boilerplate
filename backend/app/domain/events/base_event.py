from datetime import datetime, UTC
import uuid
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class DomainEvent:
    """Base class for all domain events."""

    event_type: str
    data: Dict[str, Any]

    def __post_init__(self):
        """Initialize common event properties."""
        self.event_id = str(uuid.uuid4())
        self.timestamp = datetime.now(UTC)
        self.data['timestamp'] = self.timestamp
