import logging
from typing import Dict, Any

from pydantic import BaseModel

from ..provider import BaseProvider, ProviderError
from ..types import ChatCompletionRequest, ChatCompletionResponse, Choice, ChatCompletionMessage
from ...http_client import AsyncHttpClient


class AnthropicCompletionRequest(BaseModel):
    model: str
    prompt: str
    temperature: float
    max_tokens_to_sample: int


class AnthropicCompletionResponse(BaseModel):
    completion: str
    model: str
    stop_reason: str


class AnthropicProvider(BaseProvider):
    def __init__(self, config: Dict[str, Any], http_client: AsyncHttpClient):
        self._config = config
        self._http_client = http_client
        self._logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def _check_config(config: Dict[str, Any]) -> None:
        required_keys = ['endpoint', 'key']
        if not all(key in config for key in required_keys):
            raise ProviderError("The Anthropic provider is not configured. Add settings to config.yml.")

    async def create_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        self._check_config(self._config)

        # Format the prompt
        system_prompts = []
        prompts = []
        for message in request.messages:
            if message.role == "system":
                system_prompts.append(message.content)
            elif message.role == "user":
                prompts.append(f"Human: {message.content}")
            elif message.role == "assistant":
                prompts.append(f"Assistant: {message.content}")
            else:
                self._logger.error(f"Unknown role {message.role}")

        system_prompts.append("")
        prompts.append("Assistant:")
        prompt = "\n".join(system_prompts) + "\n\n" + "\n\n".join(prompts)

        # Map and send the request
        a_request = AnthropicCompletionRequest(model=request.model,
                                               prompt=prompt,
                                               temperature=request.temperature,
                                               max_tokens_to_sample=request.max_tokens)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": self._config['key'],
            "anthropic-version": "2023-06-01"
        }
        url = self._http_client.urljoin(self._config["endpoint"], "/complete")
        data = await self._http_client.post(url, headers, a_request.model_dump_json(exclude_none=True))

        # Map and return the response
        a_response = AnthropicCompletionResponse(**data)
        finish_reason = "stop" if a_response.stop_reason == "stop_sequence" else a_response.stop_reason
        message = ChatCompletionMessage(role="assistant", content=a_response.completion)
        choice = Choice(index=0, message=message, finish_reason=finish_reason)
        response = ChatCompletionResponse(id="", object="object", created=0, choices=[choice])

        return response
