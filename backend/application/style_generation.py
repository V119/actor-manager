from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
import json
import logging
import mimetypes
from pathlib import Path
import re
from typing import Any
import urllib.error
import urllib.request

from backend.infrastructure.config import settings


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class StyledImageGenerationResult:
    image_bytes: bytes
    mime_type: str
    prompt_used: str
    prompt_template_key: str


@dataclass
class StyleReferenceImage:
    data: bytes
    filename: str


class StylePromptManager:
    def __init__(self, root_dir: str, default_dir: str, file_name: str):
        prompt_root = Path(root_dir)
        if not prompt_root.is_absolute():
            prompt_root = PROJECT_ROOT / prompt_root
        self.root_dir = prompt_root
        self.default_dir = default_dir
        self.file_name = file_name

    def resolve_prompt(self, style_id: int, style_name: str, style_category: str) -> tuple[str, str]:
        keys = self._build_prompt_keys(style_id=style_id, style_name=style_name, style_category=style_category)
        for key in keys:
            file_path = self.root_dir / key / self.file_name
            if file_path.is_file():
                return key, file_path.read_text(encoding="utf-8")

        default_path = self.root_dir / self.default_dir / self.file_name
        if default_path.is_file():
            return self.default_dir, default_path.read_text(encoding="utf-8")

        raise ValueError(
            f"风格 Prompt 文件不存在，请检查目录: {self.root_dir}，默认文件: {default_path}"
        )

    def _build_prompt_keys(self, style_id: int, style_name: str, style_category: str) -> list[str]:
        keys: list[str] = []
        category_key = self._slugify(style_category)
        name_key = self._slugify(style_name)
        if category_key:
            keys.append(category_key)
        if name_key and name_key not in keys:
            keys.append(name_key)
        keys.append(f"style_{style_id}")
        return keys

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
        return normalized


class LangChainStyleImageGenerator:
    def __init__(self):
        self.prompt_manager = StylePromptManager(
            root_dir=settings.STYLE_PROMPT_ROOT_DIR,
            default_dir=settings.STYLE_PROMPT_DEFAULT_DIR,
            file_name=settings.STYLE_PROMPT_FILE_NAME,
        )

    async def generate(
        self,
        style_id: int,
        style_name: str,
        style_description: str,
        style_category: str,
        reference_images: list[StyleReferenceImage],
        custom_prompt: str = "",
    ) -> StyledImageGenerationResult:
        self._validate_config()
        if not reference_images:
            raise ValueError("缺少风格生成参考图。")

        prompt_key, prompt_template = self.prompt_manager.resolve_prompt(
            style_id=style_id,
            style_name=style_name,
            style_category=style_category,
        )
        base_prompt = self._render_prompt_template(
            prompt_template,
            {
                "style_id": style_id,
                "style_name": style_name,
                "style_description": style_description,
                "style_category": style_category,
            },
        )
        user_prompt = (custom_prompt or "").strip()
        if user_prompt:
            base_prompt = f"{base_prompt}\n\nUser custom prompt:\n{user_prompt}"

        final_prompt = base_prompt
        if settings.STYLE_LLM_PROMPT_MODEL:
            try:
                final_prompt = await asyncio.to_thread(
                    self._refine_prompt_with_langchain,
                    base_prompt,
                    style_name,
                    style_description,
                    style_category,
                    user_prompt,
                )
            except Exception as exc:
                logger.warning("Prompt refinement failed, fallback to base prompt: %s", exc)

        image_bytes, mime_type = await asyncio.to_thread(
            self._call_image_api,
            final_prompt,
            reference_images,
        )

        logger.info(
            "Style image generated style_id=%s prompt_key=%s bytes=%s mime_type=%s",
            style_id,
            prompt_key,
            len(image_bytes),
            mime_type,
        )
        return StyledImageGenerationResult(
            image_bytes=image_bytes,
            mime_type=mime_type,
            prompt_used=final_prompt,
            prompt_template_key=prompt_key,
        )

    def _validate_config(self) -> None:
        if not settings.STYLE_GENERATION_ENABLED:
            raise ValueError("风格生成未启用，请在配置中设置 style_generation.enabled=true")
        if not settings.STYLE_LLM_BASE_URL:
            raise ValueError("缺少 style_generation.model.base_url 配置")
        if not settings.STYLE_LLM_API_KEY:
            raise ValueError("缺少 style_generation.model.api_key 配置")
        if not settings.STYLE_LLM_IMAGE_MODEL:
            raise ValueError("缺少 style_generation.model.image_model 配置")

    @staticmethod
    def _render_prompt_template(template: str, values: dict[str, Any]) -> str:
        try:
            rendered = template.format(**values)
        except Exception:
            rendered = template
        return rendered.strip()

    def _refine_prompt_with_langchain(
        self,
        base_prompt: str,
        style_name: str,
        style_description: str,
        style_category: str,
        user_custom_prompt: str,
    ) -> str:
        try:
            from langchain_core.output_parsers import StrOutputParser
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI
        except Exception as exc:
            raise RuntimeError(
                "LangChain 依赖缺失，请安装 langchain/langchain-core/langchain-openai 后重试。"
            ) from exc

        llm = ChatOpenAI(
            model=settings.STYLE_LLM_PROMPT_MODEL,
            api_key=settings.STYLE_LLM_API_KEY,
            base_url=self._resolve_prompt_base_url(),
            temperature=0.2,
            max_retries=2,
            timeout=settings.STYLE_LLM_TIMEOUT_SECONDS,
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a professional prompt engineer for image generation models."
                    " Output one concise English prompt only.",
                ),
                (
                    "human",
                    "Style name: {style_name}\n"
                    "Style description: {style_description}\n"
                    "Style category: {style_category}\n"
                    "User custom prompt: {user_custom_prompt}\n"
                    "Reference constraints: keep exact same person identity from reference image.\n"
                    "Base prompt:\n{base_prompt}\n\n"
                    "Return only a single final English prompt without markdown.",
                ),
            ]
        )
        chain = prompt | llm | StrOutputParser()
        result = chain.invoke(
            {
                "style_name": style_name,
                "style_description": style_description,
                "style_category": style_category,
                "user_custom_prompt": user_custom_prompt,
                "base_prompt": base_prompt,
            }
        )
        refined = str(result).strip()
        if not refined:
            return base_prompt
        return refined

    def _call_image_api(
        self,
        prompt: str,
        reference_images: list[StyleReferenceImage],
    ) -> tuple[bytes, str]:
        endpoint = self._compose_endpoint(settings.STYLE_LLM_BASE_URL, settings.STYLE_LLM_IMAGE_API_PATH)
        payload = {
            "model": settings.STYLE_LLM_IMAGE_MODEL,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": self._build_multimodal_content(prompt, reference_images),
                    }
                ]
            },
            "parameters": {
                "size": settings.STYLE_LLM_IMAGE_SIZE,
                "n": max(1, int(settings.STYLE_LLM_IMAGE_N)),
                "watermark": bool(settings.STYLE_LLM_IMAGE_WATERMARK),
            },
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        headers = {
            "Authorization": f"Bearer {settings.STYLE_LLM_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        req = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=settings.STYLE_LLM_TIMEOUT_SECONDS) as resp:
                response_bytes = resp.read()
                response_json = json.loads(response_bytes.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"图像生成请求失败: HTTP {exc.code} {detail}") from exc
        except Exception as exc:
            raise RuntimeError(f"图像生成请求失败: {exc}") from exc

        response_code = str(response_json.get("code") or "").strip()
        if response_code:
            message = response_json.get("message") or response_json.get("error_message") or "unknown error"
            raise RuntimeError(f"图像生成请求失败: {response_code} {message}")
        return self._parse_image_response(response_json)

    @staticmethod
    def _compose_endpoint(base_url: str, api_path: str) -> str:
        return f"{base_url.rstrip('/')}/{api_path.lstrip('/')}"

    def _resolve_prompt_base_url(self) -> str:
        configured = settings.STYLE_LLM_PROMPT_BASE_URL.strip()
        if configured:
            return configured
        base = settings.STYLE_LLM_BASE_URL.rstrip("/")
        if "dashscope.aliyuncs.com" in base and "compatible-mode" not in base:
            return f"{base}/compatible-mode/v1"
        return base

    @staticmethod
    def _to_data_uri(image_bytes: bytes, filename: str) -> str:
        guessed, _encoding = mimetypes.guess_type(filename)
        mime_type = guessed or "image/jpeg"
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"

    def _build_multimodal_content(
        self,
        prompt: str,
        reference_images: list[StyleReferenceImage],
    ) -> list[dict[str, str]]:
        content: list[dict[str, str]] = [{"text": prompt}]
        for reference in reference_images:
            content.append({"image": self._to_data_uri(reference.data, reference.filename)})
        return content

    def _parse_image_response(self, payload: dict[str, Any]) -> tuple[bytes, str]:
        if not isinstance(payload, dict):
            raise RuntimeError("图像生成响应格式非法。")

        output = payload.get("output")
        if isinstance(output, dict):
            choices = output.get("choices")
            if isinstance(choices, list):
                for choice in choices:
                    if not isinstance(choice, dict):
                        continue
                    message = choice.get("message")
                    if not isinstance(message, dict):
                        continue
                    content = message.get("content")
                    if isinstance(content, list):
                        for item in content:
                            if not isinstance(item, dict):
                                continue
                            image_bytes, mime_type = self._extract_image_from_item(item)
                            if image_bytes:
                                return image_bytes, mime_type

        data = payload.get("data")
        if isinstance(data, list) and data:
            item = data[0] if isinstance(data[0], dict) else {}
            image_bytes, mime_type = self._extract_image_from_item(item)
            if image_bytes:
                return image_bytes, mime_type

        if isinstance(output, list) and output:
            for item in output:
                if not isinstance(item, dict):
                    continue
                image_bytes, mime_type = self._extract_image_from_item(item)
                if image_bytes:
                    return image_bytes, mime_type

        raise RuntimeError(f"图像生成响应中未找到图片数据: request_id={payload.get('request_id')}")

    def _extract_image_from_item(self, item: dict[str, Any]) -> tuple[bytes, str]:
        b64_value = item.get("b64_json") or item.get("b64") or item.get("base64")
        if isinstance(b64_value, str) and b64_value:
            try:
                return base64.b64decode(b64_value), "image/png"
            except Exception as exc:
                raise RuntimeError("图片 base64 解码失败。") from exc

        image_url = item.get("url")
        if isinstance(image_url, str) and image_url:
            if image_url.startswith("data:"):
                return self._decode_data_uri(image_url)
            return self._download_remote_image(image_url)

        image_value = item.get("image")
        if isinstance(image_value, str) and image_value:
            if image_value.startswith("data:"):
                return self._decode_data_uri(image_value)
            return self._download_remote_image(image_value)
        if isinstance(image_value, dict):
            image_url = image_value.get("url")
            if isinstance(image_url, str) and image_url:
                return self._download_remote_image(image_url)

        image_url_value = item.get("image_url")
        if isinstance(image_url_value, str) and image_url_value:
            return self._download_remote_image(image_url_value)
        if isinstance(image_url_value, dict):
            image_url = image_url_value.get("url")
            if isinstance(image_url, str) and image_url:
                return self._download_remote_image(image_url)

        return b"", ""

    @staticmethod
    def _decode_data_uri(data_uri: str) -> tuple[bytes, str]:
        prefix, sep, encoded = data_uri.partition(",")
        if not sep or ";base64" not in prefix:
            raise RuntimeError("Data URI 格式非法。")
        mime_type = "image/png"
        if prefix.startswith("data:"):
            mime_type = prefix[5:].split(";")[0] or mime_type
        try:
            return base64.b64decode(encoded), mime_type
        except Exception as exc:
            raise RuntimeError("Data URI 解码失败。") from exc

    def _download_remote_image(self, image_url: str) -> tuple[bytes, str]:
        req = urllib.request.Request(image_url, method="GET")
        with urllib.request.urlopen(req, timeout=settings.STYLE_LLM_TIMEOUT_SECONDS) as resp:
            content_type = resp.headers.get("Content-Type", "image/png")
            image_bytes = resp.read()
        return image_bytes, content_type
