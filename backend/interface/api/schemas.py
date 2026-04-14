from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

VideoTypeLiteral = Literal["intro", "showreel"]


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


class ActorBasicInfoSchema(BaseModel):
    actor_id: int
    external_id: str
    name: str
    age: int
    height: int
    weight_kg: int
    location: str
    hometown: str
    bust_cm: int
    waist_cm: int
    hip_cm: int
    shoe_size: str
    bio: str
    tags: List[str]
    acting_requirements: str
    rejected_requirements: str
    availability_note: str
    avatar_url: Optional[str]
    avatar_source: Literal["three_view", "none"]
    created_at: datetime


class ActorBasicInfoUpdateRequest(BaseModel):
    name: str
    age: int = 0
    height: int = 0
    weight_kg: int = 0
    location: str = ""
    hometown: str = ""
    bust_cm: int = 0
    waist_cm: int = 0
    hip_cm: int = 0
    shoe_size: str = ""
    bio: str = ""
    tags: List[str] = Field(default_factory=list)
    acting_requirements: str = ""
    rejected_requirements: str = ""
    availability_note: str = ""

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
    style_name: str
    style_category: str
    image_url: str
    preview_url: str
    lifecycle_state: str
    published_at: Optional[datetime]
    created_at: datetime

class ProtocolSchema(BaseModel):
    id: int
    actor_id: Optional[int]
    company_name: str
    title: str
    content: str
    status: str
    created_at: datetime
    signed_at: Optional[datetime]

    class Config:
        from_attributes = True

class GenerateStyleRequest(BaseModel):
    style_id: int
    actor_id: Optional[int] = None


class StylePublishRequest(BaseModel):
    style_id: int


class StyleResultGroupSchema(BaseModel):
    style_id: int
    style_name: str
    style_category: str
    draft_result: Optional[GeneratedResultSchema]
    published_result: Optional[GeneratedResultSchema]


class StyleResultGroupListSchema(BaseModel):
    groups: List[StyleResultGroupSchema]


class ThreeViewRawImageSchema(BaseModel):
    id: int
    view_angle: Literal["front", "left", "right"]
    image_url: str
    preview_url: str
    bucket_name: str
    object_key: str
    source_filename: str
    mime_type: str
    file_size: int
    width: int
    height: int
    expected_ratio: str
    created_at: datetime


class ThreeViewUploadSchema(BaseModel):
    session_id: int
    session_key: str
    actor_id: int
    is_current: bool
    superseded_at: Optional[datetime]
    composite_image_url: str
    composite_preview_url: str
    composite_bucket: str
    composite_object_key: str
    composite_width: int
    composite_height: int
    expected_composite_ratio: str
    expected_single_ratio: str
    detection_note: str
    raw_images: List[ThreeViewRawImageSchema]
    created_at: datetime


class ThreeViewHistorySchema(BaseModel):
    items: List[ThreeViewUploadSchema]


class ThreeViewStateSchema(BaseModel):
    draft: Optional[ThreeViewUploadSchema]
    published: Optional[ThreeViewUploadSchema]


class ThreeViewDirectUploadFileSchema(BaseModel):
    view_angle: Literal["front", "left", "right"]
    filename: str
    content_type: str
    size: int = 0


class DirectUploadTargetSchema(BaseModel):
    view_angle: str
    bucket_name: str
    object_key: str
    source_filename: str
    mime_type: str
    file_size: int
    image_url: str
    upload_url: str
    upload_method: str


class ThreeViewDirectUploadPlanRequest(BaseModel):
    files: List[ThreeViewDirectUploadFileSchema]


class ThreeViewDirectUploadPlanSchema(BaseModel):
    upload_plan_token: str
    upload_batch_key: str
    expires_in_seconds: int
    uploads: List[DirectUploadTargetSchema]


class ThreeViewComposeJobCreateRequest(BaseModel):
    upload_plan_token: str
    reuse_latest_missing: bool = False


class ThreeViewComposeJobSchema(BaseModel):
    job_key: str
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    result: Optional[ThreeViewUploadSchema] = None


class PortraitVideoSchema(BaseModel):
    id: int
    actor_id: int
    user_id: int
    video_type: VideoTypeLiteral
    is_current: bool
    superseded_at: Optional[datetime]
    bucket_name: str
    object_key: str
    video_url: str
    preview_url: str
    source_filename: str
    mime_type: str
    file_size: int
    created_at: datetime


class PortraitVideoListSchema(BaseModel):
    items: List[PortraitVideoSchema]


class PortraitVideoTypeStateSchema(BaseModel):
    draft: Optional[PortraitVideoSchema]
    published: Optional[PortraitVideoSchema]


class PortraitVideoStateSchema(BaseModel):
    intro: PortraitVideoTypeStateSchema
    showreel: PortraitVideoTypeStateSchema
    both_published_ready: bool


class PortraitVideoDirectUploadPlanRequest(BaseModel):
    video_type: VideoTypeLiteral
    filename: str
    content_type: str
    size: int = 0


class PortraitVideoDirectUploadPlanSchema(BaseModel):
    upload_plan_token: str
    upload_batch_key: str
    expires_in_seconds: int
    upload: DirectUploadTargetSchema


class PortraitVideoDirectUploadCommitRequest(BaseModel):
    upload_plan_token: str


class PortraitVideoPublishRequest(BaseModel):
    video_type: VideoTypeLiteral


class HistoryCleanupResultSchema(BaseModel):
    deleted_records: int
    deleted_objects: int
    skipped_objects: int


class PublishedActorCardSchema(BaseModel):
    actor_id: int
    name: str
    external_id: str
    tags: List[str]
    cover_image_url: Optional[str]
    published_three_view_url: Optional[str]
    published_video_url: Optional[str]
    published_style_count: int
    updated_at: datetime


class PublishedActorDetailSchema(BaseModel):
    actor: ActorSchema
    published_three_view: Optional[ThreeViewUploadSchema]
    published_video: Optional[PortraitVideoSchema]
    published_videos: List[PortraitVideoSchema]
    published_styles: List[GeneratedResultSchema]
