from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PortraitSchema(BaseModel):
    id: Optional[int]
    actor_id: int
    image_url: str
    portrait_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class ActorSchema(BaseModel):
    id: Optional[int]
    name: str
    external_id: str
    age: int
    location: str
    height: int
    bio: str
    tags: List[str]
    is_published: bool
    created_at: datetime

    class Config:
        from_attributes = True

class StyleSchema(BaseModel):
    id: int
    name: str
    description: str
    preview_url: str
    category: str

    class Config:
        from_attributes = True

class GeneratedResultSchema(BaseModel):
    id: int
    actor_id: int
    style_id: int
    image_url: str
    created_at: datetime

    class Config:
        from_attributes = True

class ProtocolSchema(BaseModel):
    id: int
    actor_id: int
    company_name: str
    title: str
    content: str
    status: str
    created_at: datetime
    signed_at: Optional[datetime]

    class Config:
        from_attributes = True

class GenerateStyleRequest(BaseModel):
    actor_id: int
    style_id: int
