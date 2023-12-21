import logging
import re
from typing import Dict, Any, Optional, List, Literal

from pydantic import BaseModel

from ..provider import BaseProvider, ProviderError
from ..types import ChatCompletionRequest, ChatCompletionResponse, ChatCompletionMessage, Choice, Error
from ...http_client import AsyncHttpClient


class InlineData(BaseModel):
    mimeType: str
    data: str


class Part(BaseModel):
    text: Optional[str] = None
    inlineData: Optional[InlineData] = None


class Content(BaseModel):
    role: Literal["user", "model"]
    parts: List[Part]


class GenerationConfig(BaseModel):
    temperature: float = 0.5
    maxOutputTokens: int = 1000


class GeminiCompletionRequest(BaseModel):
    contents: List[Content]
    generationConfig: GenerationConfig


class ResponseCandidate(BaseModel):
    content: Content
    finishReason: Literal["STOP"]


class GeminiCompletionResponse(BaseModel):
    candidates: List[ResponseCandidate]


class GeminiProvider(BaseProvider):
    def __init__(self, config: Dict[str, Any], http_client: AsyncHttpClient):
        self._config = config
        self._http_client = http_client
        self._logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def _check_config(config: Dict[str, Any]) -> None:
        required_keys = ['endpoint', 'key']
        if not all(key in config for key in required_keys):
            raise ProviderError(400, "The Gemini provider is not configured. Add settings to config.yml.")

    async def create_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        self._check_config(self._config)

        g_messages = []
        role_parts = []
        role = None

        for message in request.messages:
            message_role = message.role if message.role != "system" else "user"
            if role and message_role != role:
                g_role = "user" if role == "user" else "model"
                g_messages.append(Content(role=g_role, parts=role_parts))
                role_parts = []
            role = message_role
            if isinstance(message.content, list):
                for content in message.content:
                    if content.type == "text":
                        role_parts.append(Part(text=content.text))
                    elif content.type == "image_url":
                        match = re.match(r"data:(.*?);base64,(.*)", content.image_url)
                        if match.groups():
                            mime_type = match.group(1)
                            data = match.group(2)
                            role_parts.append(Part(inlineData=InlineData(mimeType=mime_type, data=data)))
                    else:
                        self._logger.error(f"Unknown content type {content.type}")
            else:
                role_parts.append(Part(text=message.content))

        if role_parts:
            g_role = "user" if role == "user" else "model"
            g_messages.append(Content(role=g_role, parts=role_parts))

        g_config = GenerationConfig(temperature=request.temperature,
                                    maxOutputTokens=request.max_tokens)

        g_request = GeminiCompletionRequest(contents=g_messages,
                                            generationConfig=g_config)

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-goog-api-key": self._config['key']
        }
        url = self._http_client.urljoin(self._config["endpoint"], "/models", f"{request.model}:generateContent")
        data = await self._http_client.post(url, headers, g_request.model_dump_json(exclude_none=True))

        if "error" in data:
            error = Error(**data['error'])
            raise ProviderError(error.code, error.message)
        else:
            g_response = GeminiCompletionResponse(**data)
            g_candidate = g_response.candidates[0]
            finish_reason = "stop" if g_candidate.finishReason == "STOP" else g_candidate.finishReason
            message = ChatCompletionMessage(role="assistant", content=g_candidate.content.parts[0].text)
            choice = Choice(index=0, message=message, finish_reason=finish_reason)
            response = ChatCompletionResponse(id="", object="object", created=0, choices=[choice])

            return response
