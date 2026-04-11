from typing import List, Optional
from peewee_async import Manager
from ..domain.models import Actor, Portrait, Style, GeneratedResult, Protocol, ProtocolStatus
from ..domain.repositories import (
    ActorRepository, PortraitRepository, StyleRepository,
    GeneratedResultRepository, ProtocolRepository
)
from .orm_models import ActorModel, PortraitModel, StyleModel, GeneratedResultModel, ProtocolModel

class PeeweeActorRepository(ActorRepository):
    def __init__(self, manager: Manager):
        self.manager = manager

    async def get_by_id(self, actor_id: int) -> Optional[Actor]:
        try:
            model = await self.manager.get(ActorModel, id=actor_id)
            return self._to_domain(model)
        except ActorModel.DoesNotExist:
            return None

    async def list_actors(self, skip: int = 0, limit: int = 20, tag: Optional[str] = None) -> List[Actor]:
        query = ActorModel.select().offset(skip).limit(limit)
        if tag:
            # Simple tag filtering for demonstration
            query = query.where(ActorModel.tags.contains(tag))
        models = await self.manager.execute(query)
        return [self._to_domain(m) for m in models]

    async def save(self, actor: Actor) -> Actor:
        data = {
            'name': actor.name,
            'external_id': actor.external_id,
            'age': actor.age,
            'location': actor.location,
            'height': actor.height,
            'bio': actor.bio,
            'tags': actor.tags,
            'is_published': actor.is_published
        }
        if actor.id:
            await self.manager.execute(ActorModel.update(**data).where(ActorModel.id == actor.id))
            model = await self.manager.get(ActorModel, id=actor.id)
        else:
            model = await self.manager.create(ActorModel, **data)
        return self._to_domain(model)

    def _to_domain(self, model: ActorModel) -> Actor:
        return Actor(
            id=model.id,
            name=model.name,
            external_id=model.external_id,
            age=model.age,
            location=model.location,
            height=model.height,
            bio=model.bio,
            tags=model.tags,
            is_published=model.is_published,
            created_at=model.created_at
        )

class PeeweePortraitRepository(PortraitRepository):
    def __init__(self, manager: Manager):
        self.manager = manager

    async def get_by_actor(self, actor_id: int) -> List[Portrait]:
        query = PortraitModel.select().where(PortraitModel.actor_id == actor_id)
        models = await self.manager.execute(query)
        return [self._to_domain(m) for m in models]

    async def save(self, portrait: Portrait) -> Portrait:
        model = await self.manager.create(
            PortraitModel,
            actor_id=portrait.actor_id,
            image_url=portrait.image_url,
            portrait_type=portrait.portrait_type
        )
        return self._to_domain(model)

    def _to_domain(self, model: PortraitModel) -> Portrait:
        return Portrait(
            id=model.id,
            actor_id=model.actor_id,
            image_url=model.image_url,
            portrait_type=model.portrait_type,
            created_at=model.created_at
        )

class PeeweeStyleRepository(StyleRepository):
    def __init__(self, manager: Manager):
        self.manager = manager

    async def list_styles(self) -> List[Style]:
        models = await self.manager.execute(StyleModel.select())
        return [self._to_domain(m) for m in models]

    async def get_by_id(self, style_id: int) -> Optional[Style]:
        try:
            model = await self.manager.get(StyleModel, id=style_id)
            return self._to_domain(model)
        except StyleModel.DoesNotExist:
            return None

    def _to_domain(self, model: StyleModel) -> Style:
        return Style(
            id=model.id,
            name=model.name,
            description=model.description,
            preview_url=model.preview_url,
            category=model.category
        )

class PeeweeGeneratedResultRepository(GeneratedResultRepository):
    def __init__(self, manager: Manager):
        self.manager = manager

    async def list_by_actor(self, actor_id: int) -> List[GeneratedResult]:
        query = GeneratedResultModel.select().where(GeneratedResultModel.actor_id == actor_id)
        models = await self.manager.execute(query)
        return [self._to_domain(m) for m in models]

    async def save(self, result: GeneratedResult) -> GeneratedResult:
        model = await self.manager.create(
            GeneratedResultModel,
            actor_id=result.actor_id,
            style_id=result.style_id,
            image_url=result.image_url
        )
        return self._to_domain(model)

    def _to_domain(self, model: GeneratedResultModel) -> GeneratedResult:
        return GeneratedResult(
            id=model.id,
            actor_id=model.actor_id,
            style_id=model.style_id,
            image_url=model.image_url,
            created_at=model.created_at
        )

class PeeweeProtocolRepository(ProtocolRepository):
    def __init__(self, manager: Manager):
        self.manager = manager

    async def list_by_actor(self, actor_id: int) -> List[Protocol]:
        query = ProtocolModel.select().where(ProtocolModel.actor_id == actor_id)
        models = await self.manager.execute(query)
        return [self._to_domain(m) for m in models]

    async def get_by_id(self, protocol_id: int) -> Optional[Protocol]:
        try:
            model = await self.manager.get(ProtocolModel, id=protocol_id)
            return self._to_domain(model)
        except ProtocolModel.DoesNotExist:
            return None

    async def update_status(self, protocol_id: int, status: str) -> bool:
        from datetime import datetime
        update_data = {'status': status}
        if status == 'signed':
            update_data['signed_at'] = datetime.now()

        updated = await self.manager.execute(
            ProtocolModel.update(**update_data).where(ProtocolModel.id == protocol_id)
        )
        return updated > 0

    def _to_domain(self, model: ProtocolModel) -> Protocol:
        return Protocol(
            id=model.id,
            actor_id=model.actor_id,
            company_name=model.company_name,
            title=model.title,
            content=model.content,
            status=ProtocolStatus(model.status),
            created_at=model.created_at,
            signed_at=model.signed_at
        )
