import pytest
from backend.domain.models import Actor, Portrait
from backend.application.services import ActorService, PortraitService

class MockActorRepo:
    async def get_by_id(self, aid):
        return Actor(aid, "Test", "GL-1", 20, "Loc", 180, "Bio")
    async def list_actors(self, tag=None):
        return []
    async def save(self, actor):
        actor.id = 1
        return actor

@pytest.mark.asyncio
async def test_actor_service_get():
    repo = MockActorRepo()
    service = ActorService(repo)
    actor = await service.get_actor(1)
    assert actor.name == "Test"

@pytest.mark.asyncio
async def test_actor_service_list():
    repo = MockActorRepo()
    service = ActorService(repo)
    actors = await service.list_actors()
    assert isinstance(actors, list)
