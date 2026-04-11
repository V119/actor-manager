from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List, Optional
from backend.interface.api.schemas import ActorSchema, PortraitSchema, StyleSchema, GeneratedResultSchema, ProtocolSchema, GenerateStyleRequest
from backend.application.services import ActorService, PortraitService, StyleService, ProtocolService
from backend.infrastructure.repositories import (
    PeeweeActorRepository, PeeweePortraitRepository,
    PeeweeStyleRepository, PeeweeProtocolRepository,
    PeeweeGeneratedResultRepository
)
from backend.infrastructure.orm_models import database

router = APIRouter()

def get_actor_service():
    return ActorService(PeeweeActorRepository())

def get_portrait_service():
    from backend.infrastructure.storage import StorageClient
    from backend.infrastructure.config import settings
    storage_client = StorageClient(
        settings.MINIO_ENDPOINT,
        settings.MINIO_ACCESS_KEY,
        settings.MINIO_SECRET_KEY,
        settings.MINIO_BUCKET
    )
    return PortraitService(PeeweePortraitRepository(), storage_client)

def get_style_service():
    return StyleService(
        PeeweeStyleRepository(),
        PeeweeGeneratedResultRepository()
    )

def get_protocol_service():
    return ProtocolService(PeeweeProtocolRepository())

@router.get("/actors", response_model=List[ActorSchema])
async def list_actors(tag: Optional[str] = None, service: ActorService = Depends(get_actor_service)):
    return await service.list_actors(tag=tag)

@router.get("/actors/{actor_id}", response_model=ActorSchema)
async def get_actor(actor_id: int, service: ActorService = Depends(get_actor_service)):
    actor = await service.get_actor(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")
    return actor

@router.post("/portraits", response_model=PortraitSchema)
async def upload_portrait(
    actor_id: int,
    portrait_type: str,
    file: UploadFile = File(...),
    service: PortraitService = Depends(get_portrait_service)
):
    data = await file.read()
    return await service.upload_portrait(actor_id, portrait_type, data, file.filename)

@router.get("/styles", response_model=List[StyleSchema])
async def list_styles(service: StyleService = Depends(get_style_service)):
    return await service.list_styles()

@router.post("/styles/generate", response_model=GeneratedResultSchema)
async def generate_style(req: GenerateStyleRequest, service: StyleService = Depends(get_style_service)):
    return await service.generate_result(req.actor_id, req.style_id)

@router.get("/protocols", response_model=List[ProtocolSchema])
async def list_protocols(actor_id: int, service: ProtocolService = Depends(get_protocol_service)):
    return await service.list_protocols(actor_id)

@router.post("/protocols/{protocol_id}/sign")
async def sign_protocol(protocol_id: int, service: ProtocolService = Depends(get_protocol_service)):
    success = await service.sign_protocol(protocol_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to sign protocol")
    return {"message": "Protocol signed successfully"}
