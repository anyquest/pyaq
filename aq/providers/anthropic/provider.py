import logging
from typing import Dict, Any, Literal, List

from pydantic import BaseModel

from ..provider import BaseProvider, ProviderError
from ..types import ChatCompletionRequest, ChatCompletionResponse, Choice, ChatCompletionMessage, Content, Error, Usage
from ...http_client import AsyncHttpClient


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AnthropicCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    system: str
    temperature: float
    max_tokens: int


class AnthropicCompletionResponse(BaseModel):
    type: Literal["message"]
    role: Literal["assistant"]
    content: List[Content]
    model: str
    stop_reason: str


class AnthropicProvider(BaseProvider):
    def __init__(self, config: Dict[str, Any], http_client: AsyncHttpClient):
        self._config = config
        self._http_client = http_client
        self._logger = logging.getLogger(self.__class__.__name__)

    async def create_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        self._check_config(self._config)

        # Format the prompt
        messages = []
        system_prompts = []
        for message in request.messages:
            if message.role == "system":
                system_prompts.append(message.content)
            else:
                messages.append(self._msg2msg(message))

        # Map and send the request
        a_request = AnthropicCompletionRequest(model=request.model,
                                               messages=messages,
                                               system="\n".join(system_prompts) if system_prompts else None,
                                               temperature=request.temperature,
                                               max_tokens=request.max_tokens)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": self._config['key'],
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "messages-2023-12-15"
        }
        url = self._http_client.urljoin(self._config["endpoint"], "/messages")
        data = await self._http_client.post(url, headers, a_request.model_dump_json(exclude_none=True))

        if "error" in data:
            error = Error(**data['error'])
            raise ProviderError(error.code, error.message)
        else:
            # Map and return the response
            a_response = AnthropicCompletionResponse(**data)
            finish_reason = "stop" if a_response.stop_reason == "end_turn" else a_response.stop_reason
            if a_response.content:
                usage = Usage()
                message = ChatCompletionMessage(role="assistant", content=a_response.content[0].text)
                choice = Choice(index=0, message=message, finish_reason=finish_reason)
                return ChatCompletionResponse(id="", object="object", created=0, choices=[choice], usage=usage)
            else:
                raise ProviderError(500, "Could not parse the response")

    @staticmethod
    def _check_config(config: Dict[str, Any]) -> None:
        required_keys = ['endpoint', 'key']
        if not all(key in config for key in required_keys):
            raise ProviderError(400, "The Anthropic provider is not configured. Add settings to config.yml.")

    @staticmethod
    def _msg2msg(message: ChatCompletionMessage) -> Message:
        if isinstance(message.content, str):
            return Message(role=message.role, content=message.content)
        elif isinstance(message.content, list):
            content = "\n".join([c.text for c in message.content if c.type == "text"])
            if content:
                return Message(role=message.role, content=content)
        raise ProviderError(400, "Invalid message")
