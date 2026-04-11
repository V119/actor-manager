from typing import List, Optional
from backend.domain.models import Actor, Portrait, Style, GeneratedResult, Protocol, ProtocolStatus
from backend.domain.repositories import (
    ActorRepository, PortraitRepository, StyleRepository,
    GeneratedResultRepository, ProtocolRepository
)
from backend.infrastructure.storage import StorageClient

class ActorService:
    def __init__(self, actor_repo: ActorRepository):
        self.actor_repo = actor_repo

    async def get_actor(self, actor_id: int) -> Optional[Actor]:
        return await self.actor_repo.get_by_id(actor_id)

    async def list_actors(self, tag: Optional[str] = None) -> List[Actor]:
        return await self.actor_repo.list_actors(tag=tag)

class PortraitService:
    def __init__(self, portrait_repo: PortraitRepository, storage_client: StorageClient):
        self.portrait_repo = portrait_repo
        self.storage_client = storage_client

    async def upload_portrait(self, actor_id: int, portrait_type: str, file_data: bytes, filename: str) -> Portrait:
        image_url = await self.storage_client.upload_file(
            f"actors/{actor_id}/{filename}",
            file_data,
            "image/jpeg"
        )
        portrait = Portrait(
            id=None,
            actor_id=actor_id,
            image_url=image_url,
            portrait_type=portrait_type
        )
        return await self.portrait_repo.save(portrait)

    async def get_actor_portraits(self, actor_id: int) -> List[Portrait]:
        return await self.portrait_repo.get_by_actor(actor_id)

class StyleService:
    def __init__(self, style_repo: StyleRepository, result_repo: GeneratedResultRepository):
        self.style_repo = style_repo
        self.result_repo = result_repo

    async def list_styles(self) -> List[Style]:
        return await self.style_repo.list_styles()

    async def generate_result(self, actor_id: int, style_id: int) -> GeneratedResult:
        # Mocking AI generation logic
        mock_url = f"generated/{actor_id}_{style_id}.jpg"
        result = GeneratedResult(
            id=None,
            actor_id=actor_id,
            style_id=style_id,
            image_url=mock_url
        )
        return await self.result_repo.save(result)

    async def list_results(self, actor_id: int) -> List[GeneratedResult]:
        return await self.result_repo.list_by_actor(actor_id)

class ProtocolService:
    def __init__(self, protocol_repo: ProtocolRepository):
        self.protocol_repo = protocol_repo

    async def list_protocols(self, actor_id: int) -> List[Protocol]:
        return await self.protocol_repo.list_by_actor(actor_id)

    async def get_protocol(self, protocol_id: int) -> Optional[Protocol]:
        return await self.protocol_repo.get_by_id(protocol_id)

    async def sign_protocol(self, protocol_id: int) -> bool:
        return await self.protocol_repo.update_status(protocol_id, "signed")

    async def reject_protocol(self, protocol_id: int) -> bool:
        return await self.protocol_repo.update_status(protocol_id, "rejected")
