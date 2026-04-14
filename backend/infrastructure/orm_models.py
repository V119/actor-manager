import peewee
import peewee_async
from datetime import datetime
from playhouse.postgres_ext import BinaryJSONField

database = peewee_async.PooledPostgresqlDatabase(None)

class BaseModel(peewee_async.AioModel):
    class Meta:
        database = database

class ActorModel(BaseModel):
    name = peewee.CharField()
    external_id = peewee.CharField(unique=True)
    age = peewee.IntegerField()
    location = peewee.CharField()
    hometown = peewee.CharField(default="")
    height = peewee.IntegerField()
    weight_kg = peewee.IntegerField(default=0)
    bust_cm = peewee.IntegerField(default=0)
    waist_cm = peewee.IntegerField(default=0)
    hip_cm = peewee.IntegerField(default=0)
    shoe_size = peewee.CharField(default="")
    bio = peewee.TextField()
    acting_requirements = peewee.TextField(default="")
    rejected_requirements = peewee.TextField(default="")
    availability_note = peewee.TextField(default="")
    tags = BinaryJSONField(default=[])
    is_published = peewee.BooleanField(default=False)
    created_at = peewee.DateTimeField(default=datetime.now)

class PortraitModel(BaseModel):
    actor = peewee.ForeignKeyField(ActorModel, backref='portraits')
    image_url = peewee.CharField()
    portrait_type = peewee.CharField()
    created_at = peewee.DateTimeField(default=datetime.now)

class StyleModel(BaseModel):
    name = peewee.CharField()
    description = peewee.TextField()
    preview_url = peewee.CharField()
    category = peewee.CharField()

class UserModel(BaseModel):
    username = peewee.CharField(unique=True)
    password_hash = peewee.CharField()
    role = peewee.CharField()  # "individual" | "enterprise" | "admin"
    display_name = peewee.CharField()
    company_intro = peewee.TextField(default="")
    created_at = peewee.DateTimeField(default=datetime.now)


class PortraitGuidanceSampleModel(BaseModel):
    view_angle = peewee.CharField(unique=True, index=True)  # left | front | right
    bucket_name = peewee.CharField()
    object_key = peewee.CharField()
    image_url = peewee.CharField()
    source_filename = peewee.CharField()
    mime_type = peewee.CharField()
    file_size = peewee.BigIntegerField(default=0)
    created_at = peewee.DateTimeField(default=datetime.now)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)


class GeneratedResultModel(BaseModel):
    actor = peewee.ForeignKeyField(ActorModel)
    user = peewee.ForeignKeyField(UserModel, backref='generated_results', on_delete='CASCADE', null=True)
    style = peewee.ForeignKeyField(StyleModel)
    image_url = peewee.CharField()
    lifecycle_state = peewee.CharField(default='draft', index=True)  # draft | published | superseded
    superseded_at = peewee.DateTimeField(null=True, index=True)
    published_at = peewee.DateTimeField(null=True, index=True)
    created_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('actor', 'user', 'style', 'lifecycle_state', 'created_at'), False),
        )

class SessionModel(BaseModel):
    user = peewee.ForeignKeyField(UserModel, backref='sessions', on_delete='CASCADE')
    token = peewee.CharField(unique=True, index=True)
    expires_at = peewee.DateTimeField()
    created_at = peewee.DateTimeField(default=datetime.now)

class ProtocolModel(BaseModel):
    actor = peewee.ForeignKeyField(ActorModel, null=True)
    enterprise_user = peewee.ForeignKeyField(UserModel, backref='created_protocols', null=True)
    target_user = peewee.ForeignKeyField(UserModel, backref='assigned_protocols', null=True)
    company_name = peewee.CharField()
    title = peewee.CharField()
    content = peewee.TextField()
    status = peewee.CharField(default='pending')
    created_at = peewee.DateTimeField(default=datetime.now)
    signed_at = peewee.DateTimeField(null=True)


class PortraitUploadSessionModel(BaseModel):
    actor = peewee.ForeignKeyField(ActorModel, backref='portrait_upload_sessions')
    user = peewee.ForeignKeyField(UserModel, backref='portrait_upload_sessions', on_delete='CASCADE')
    session_key = peewee.CharField(unique=True, index=True)
    is_current = peewee.BooleanField(default=True, index=True)
    superseded_at = peewee.DateTimeField(null=True, index=True)
    composite_bucket = peewee.CharField()
    composite_object_key = peewee.CharField()
    composite_image_url = peewee.CharField()
    composite_width = peewee.IntegerField()
    composite_height = peewee.IntegerField()
    created_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('actor', 'user', 'created_at'), False),
        )


class PortraitUploadAssetModel(BaseModel):
    session = peewee.ForeignKeyField(PortraitUploadSessionModel, backref='raw_assets', on_delete='CASCADE')
    actor = peewee.ForeignKeyField(ActorModel, backref='portrait_upload_assets')
    user = peewee.ForeignKeyField(UserModel, backref='portrait_upload_assets', on_delete='CASCADE')
    view_angle = peewee.CharField()
    bucket_name = peewee.CharField()
    object_key = peewee.CharField()
    image_url = peewee.CharField()
    source_filename = peewee.CharField()
    mime_type = peewee.CharField()
    file_size = peewee.BigIntegerField(default=0)
    width = peewee.IntegerField()
    height = peewee.IntegerField()
    expected_ratio = peewee.CharField(default='9:16')
    created_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('session', 'view_angle'), True),
            (('actor', 'user', 'created_at'), False),
        )


class PortraitVideoAssetModel(BaseModel):
    actor = peewee.ForeignKeyField(ActorModel, backref='portrait_video_assets')
    user = peewee.ForeignKeyField(UserModel, backref='portrait_video_assets', on_delete='CASCADE')
    video_type = peewee.CharField(default='intro', index=True)
    is_current = peewee.BooleanField(default=True, index=True)
    superseded_at = peewee.DateTimeField(null=True, index=True)
    bucket_name = peewee.CharField()
    object_key = peewee.CharField()
    video_url = peewee.CharField()
    source_filename = peewee.CharField()
    mime_type = peewee.CharField()
    file_size = peewee.BigIntegerField(default=0)
    created_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('actor', 'user', 'video_type', 'created_at'), False),
        )


class PortraitComposeJobModel(BaseModel):
    job_key = peewee.CharField(unique=True, index=True)
    actor = peewee.ForeignKeyField(ActorModel, backref='portrait_compose_jobs')
    user = peewee.ForeignKeyField(UserModel, backref='portrait_compose_jobs', on_delete='CASCADE')
    status = peewee.CharField(default='pending', index=True)  # pending | processing | completed | failed
    request_payload = BinaryJSONField(default=dict)
    result_session = peewee.ForeignKeyField(PortraitUploadSessionModel, null=True, backref='compose_jobs')
    error_message = peewee.TextField(null=True)
    created_at = peewee.DateTimeField(default=datetime.now, index=True)
    updated_at = peewee.DateTimeField(default=datetime.now, index=True)

    class Meta:
        indexes = (
            (('user', 'status', 'created_at'), False),
            (('status', 'created_at'), False),
        )
