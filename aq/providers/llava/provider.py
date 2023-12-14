import logging
from typing import Dict, Any

from pydantic import BaseModel

from ..provider import BaseProvider
from ..types import ChatCompletionRequest, ChatCompletionResponse, Choice, ChatCompletionMessage
from ...http_client import AsyncHttpClient


class LlavaCompletionRequest(BaseModel):
    prompt: str
    temperature: float
    n_predict: int
    cache_prompt: bool = False


class LlavaCompletionResponse(BaseModel):
    content: str
    stop: bool
    stopped_limit: bool


# A provider for llava-v1.5 available here
# https://huggingface.co/jartine/llava-v1.5-7B-GGUF/blob/main/llava-v1.5-7b-q4-server.llamafile
class LlavaProvider(BaseProvider):
    def __init__(self, config: Dict[str, Any], http_client: AsyncHttpClient):
        self._config = config
        self._http_client = http_client
        self._logger = logging.getLogger(self.__class__.__name__)

    async def create_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        # Format the prompt
        prompts = []
        for message in request.messages:
            if message.role == "user" or message.role == "system":
                prompts.append(f"User: {message.content}")
            elif message.role == "assistant":
                prompts.append(f"Llama: {message.content}")
            else:
                self._logger.error(f"Unknown role {message.role}")

        prompts.append("Llama:")
        prompt = "\n\n" + "\n".join(prompts)

        # Map and send the request
        a_request = LlavaCompletionRequest(prompt=prompt,
                                           temperature=request.temperature,
                                           n_predict=request.max_tokens)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        url = self._http_client.urljoin(self._config["endpoint"], "/completion")
        data = await self._http_client.post(url, headers, a_request.model_dump_json(exclude_none=True))

        # Map and return the response
        a_response = LlavaCompletionResponse(**data)
        finish_reason = "stop"
        if a_response.stopped_limit:
            finish_reason = "length"
        message = ChatCompletionMessage(role="assistant", content=a_response.content)
        choice = Choice(index=0, message=message, finish_reason=finish_reason)
        response = ChatCompletionResponse(id="", object="object", created=0, choices=[choice])

        return response
