from dataclasses import dataclass

from backend.config import get_config


def _parse_compose_order() -> tuple[str, str, str]:
    raw = get_config("portrait.compose.order", ["left", "front", "right"])
    if not isinstance(raw, list):
        return ("left", "front", "right")
    normalized = [str(item).strip().lower() for item in raw]
    expected = {"front", "left", "right"}
    if set(normalized) != expected:
        return ("left", "front", "right")
    return tuple(normalized)  # type: ignore[return-value]


@dataclass
class Settings:
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str
    MINIO_PUBLIC_BASE_URL: str
    MINIO_PORTRAIT_RAW_BUCKET: str
    MINIO_PORTRAIT_GENERATED_BUCKET: str
    MINIO_PORTRAIT_VIDEO_BUCKET: str
    MINIO_PORTRAIT_AUDIO_BUCKET: str
    MINIO_PORTRAIT_GUIDANCE_BUCKET: str
    MINIO_STYLE_GENERATED_BUCKET: str
    MINIO_SECURE: bool
    MINIO_PRESIGN_EXPIRES_SECONDS: int
    STREAM_UPLOAD_PART_SIZE: int
    UPLOAD_PLAN_SECRET: str
    UPLOAD_PLAN_EXPIRES_SECONDS: int
    PORTRAIT_EXPECTED_SINGLE_RATIO: str
    PORTRAIT_EXPECTED_COMPOSITE_RATIO: str
    PORTRAIT_COMPOSE_WIDTH: int
    PORTRAIT_COMPOSE_HEIGHT: int
    PORTRAIT_COMPOSE_ORDER: tuple[str, str, str]
    PORTRAIT_COMPOSE_WORKER_CONCURRENCY: int
    STYLE_GENERATION_ENABLED: bool
    STYLE_LLM_BASE_URL: str
    STYLE_LLM_PROMPT_BASE_URL: str
    STYLE_LLM_API_KEY: str
    STYLE_LLM_PROMPT_MODEL: str
    STYLE_LLM_IMAGE_MODEL: str
    STYLE_LLM_TIMEOUT_SECONDS: int
    STYLE_LLM_IMAGE_API_PATH: str
    STYLE_LLM_IMAGE_SIZE: str
    STYLE_LLM_IMAGE_N: int
    STYLE_LLM_IMAGE_WATERMARK: bool
    STYLE_LLM_IMAGE_QUALITY: str
    STYLE_LLM_IMAGE_RESPONSE_FORMAT: str
    STYLE_PROMPT_ROOT_DIR: str
    STYLE_PROMPT_DEFAULT_DIR: str
    STYLE_PROMPT_FILE_NAME: str
    STYLE_RESULTS_LIMIT_PER_STYLE: int

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings(
    DB_NAME=str(get_config("database.name", "glacier_db")),
    DB_USER=str(get_config("database.user", "postgres")),
    DB_PASSWORD=str(get_config("database.password", "postgres")),
    DB_HOST=str(get_config("database.host", "localhost")),
    DB_PORT=int(get_config("database.port", 5432)),
    MINIO_ENDPOINT=str(get_config("minio.endpoint", "localhost:9000")),
    MINIO_ACCESS_KEY=str(get_config("minio.access_key", "minioadmin")),
    MINIO_SECRET_KEY=str(get_config("minio.secret_key", "minioadmin")),
    MINIO_BUCKET=str(get_config("minio.bucket", "glacier")),
    MINIO_PUBLIC_BASE_URL=str(get_config("minio.public_base_url", "")),
    MINIO_PORTRAIT_RAW_BUCKET=str(get_config("minio.buckets.portrait_raw", "glacier-portrait-raw")),
    MINIO_PORTRAIT_GENERATED_BUCKET=str(
        get_config("minio.buckets.portrait_generated", "glacier-portrait-generated")
    ),
    MINIO_PORTRAIT_VIDEO_BUCKET=str(get_config("minio.buckets.portrait_video", "glacier-portrait-video")),
    MINIO_PORTRAIT_AUDIO_BUCKET=str(get_config("minio.buckets.portrait_audio", "glacier-portrait-audio")),
    MINIO_PORTRAIT_GUIDANCE_BUCKET=str(get_config("minio.buckets.portrait_guidance", "glacier-portrait-guidance")),
    MINIO_STYLE_GENERATED_BUCKET=str(get_config("minio.buckets.style_generated", "glacier-style-generated")),
    MINIO_SECURE=bool(get_config("minio.secure", False)),
    MINIO_PRESIGN_EXPIRES_SECONDS=int(get_config("minio.presign_expires_seconds", 1200)),
    STREAM_UPLOAD_PART_SIZE=int(get_config("upload.stream.part_size", 10485760)),
    UPLOAD_PLAN_SECRET=str(get_config("upload.plan.secret", "change-me-upload-plan-secret")),
    UPLOAD_PLAN_EXPIRES_SECONDS=int(get_config("upload.plan.expires_seconds", 1800)),
    PORTRAIT_EXPECTED_SINGLE_RATIO=str(get_config("portrait.guidance.expected_single_ratio", "9:16")),
    PORTRAIT_EXPECTED_COMPOSITE_RATIO=str(get_config("portrait.guidance.expected_composite_ratio", "4:3")),
    PORTRAIT_COMPOSE_WIDTH=int(get_config("portrait.compose.width", 1200)),
    PORTRAIT_COMPOSE_HEIGHT=int(get_config("portrait.compose.height", 900)),
    PORTRAIT_COMPOSE_ORDER=_parse_compose_order(),
    PORTRAIT_COMPOSE_WORKER_CONCURRENCY=int(get_config("portrait.compose.worker_concurrency", 2)),
    STYLE_GENERATION_ENABLED=bool(get_config("style_generation.enabled", False)),
    STYLE_LLM_BASE_URL=str(get_config("style_generation.model.base_url", "https://dashscope.aliyuncs.com")),
    STYLE_LLM_PROMPT_BASE_URL=str(get_config("style_generation.model.prompt_base_url", "")),
    STYLE_LLM_API_KEY=str(get_config("style_generation.model.api_key", "")),
    STYLE_LLM_PROMPT_MODEL=str(get_config("style_generation.model.prompt_model", "qwen-plus")),
    STYLE_LLM_IMAGE_MODEL=str(get_config("style_generation.model.image_model", "wan2.7-image")),
    STYLE_LLM_TIMEOUT_SECONDS=int(get_config("style_generation.model.timeout_seconds", 120)),
    STYLE_LLM_IMAGE_API_PATH=str(
        get_config("style_generation.model.image_api_path", "/api/v1/services/aigc/multimodal-generation/generation")
    ),
    STYLE_LLM_IMAGE_SIZE=str(get_config("style_generation.image.size", "1024*1024")),
    STYLE_LLM_IMAGE_N=int(get_config("style_generation.image.n", 1)),
    STYLE_LLM_IMAGE_WATERMARK=bool(get_config("style_generation.image.watermark", False)),
    STYLE_LLM_IMAGE_QUALITY=str(get_config("style_generation.image.quality", "high")),
    STYLE_LLM_IMAGE_RESPONSE_FORMAT=str(get_config("style_generation.image.response_format", "b64_json")),
    STYLE_PROMPT_ROOT_DIR=str(get_config("style_generation.prompts.root_dir", "backend/prompts/styles")),
    STYLE_PROMPT_DEFAULT_DIR=str(get_config("style_generation.prompts.default_dir", "default")),
    STYLE_PROMPT_FILE_NAME=str(get_config("style_generation.prompts.file_name", "prompt.txt")),
    STYLE_RESULTS_LIMIT_PER_STYLE=int(get_config("style_generation.results.limit_per_style", 20)),
)
