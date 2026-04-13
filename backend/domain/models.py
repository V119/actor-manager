from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class ProtocolStatus(Enum):
    PENDING = "pending"
    SIGNED = "signed"
    REJECTED = "rejected"

@dataclass
class Portrait:
    id: Optional[int]
    actor_id: int
    image_url: str
    portrait_type: str  # e.g., "front", "left", "right", "full_body"
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Actor:
    id: Optional[int]
    name: str
    external_id: str  # e.g., GL-928374
    age: int
    location: str
    height: int
    bio: str
    tags: List[str] = field(default_factory=list)
    portraits: List[Portrait] = field(default_factory=list)
    is_published: bool = False
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Style:
    id: Optional[int]
    name: str
    description: str
    preview_url: str
    category: str

@dataclass
class GeneratedResult:
    id: Optional[int]
    actor_id: int
    style_id: int
    image_url: str
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Protocol:
    id: Optional[int]
    actor_id: Optional[int]
    company_name: str
    title: str
    content: str
    status: ProtocolStatus = ProtocolStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    signed_at: Optional[datetime] = None
