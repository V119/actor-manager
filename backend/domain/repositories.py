from abc import ABC, abstractmethod
from typing import List, Optional
from .models import Actor, Portrait, Style, GeneratedResult, Protocol

class ActorRepository(ABC):
    @abstractmethod
    async def get_by_id(self, actor_id: int) -> Optional[Actor]:
        pass

    @abstractmethod
    async def list_actors(self, skip: int = 0, limit: int = 20, tag: Optional[str] = None) -> List[Actor]:
        pass

    @abstractmethod
    async def save(self, actor: Actor) -> Actor:
        pass

class PortraitRepository(ABC):
    @abstractmethod
    async def get_by_actor(self, actor_id: int) -> List[Portrait]:
        pass

    @abstractmethod
    async def save(self, portrait: Portrait) -> Portrait:
        pass

class StyleRepository(ABC):
    @abstractmethod
    async def list_styles(self) -> List[Style]:
        pass

    @abstractmethod
    async def get_by_id(self, style_id: int) -> Optional[Style]:
        pass

class GeneratedResultRepository(ABC):
    @abstractmethod
    async def list_by_actor(self, actor_id: int) -> List[GeneratedResult]:
        pass

    @abstractmethod
    async def save(self, result: GeneratedResult) -> GeneratedResult:
        pass

class ProtocolRepository(ABC):
    @abstractmethod
    async def list_by_actor(self, actor_id: int) -> List[Protocol]:
        pass

    @abstractmethod
    async def get_by_id(self, protocol_id: int) -> Optional[Protocol]:
        pass

    @abstractmethod
    async def update_status(self, protocol_id: int, status: str) -> bool:
        pass
