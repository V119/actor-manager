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
    height = peewee.IntegerField()
    bio = peewee.TextField()
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

class GeneratedResultModel(BaseModel):
    actor = peewee.ForeignKeyField(ActorModel)
    style = peewee.ForeignKeyField(StyleModel)
    image_url = peewee.CharField()
    created_at = peewee.DateTimeField(default=datetime.now)

class ProtocolModel(BaseModel):
    actor = peewee.ForeignKeyField(ActorModel)
    company_name = peewee.CharField()
    title = peewee.CharField()
    content = peewee.TextField()
    status = peewee.CharField(default='pending')
    created_at = peewee.DateTimeField(default=datetime.now)
    signed_at = peewee.DateTimeField(null=True)
