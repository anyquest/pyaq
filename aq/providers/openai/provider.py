import logging
from typing import Dict, Any

from ..provider import BaseProvider
from ...http_client import AsyncHttpClient
from ..types import ChatCompletionRequest, ChatCompletionResponse


class OpenAIProvider(BaseProvider):
    def __init__(self, config: Dict[str, Any], http_client: AsyncHttpClient):
        self._config = config
        self._http_client = http_client
        self._logger = logging.getLogger(self.__class__.__name__)

    async def create_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._config['key']}"
        }
        url = self._http_client.urljoin(self._config["endpoint"], "/chat/completions")
        response = await self._http_client.post(url, headers, request.model_dump_json(exclude_none=True))
        return ChatCompletionResponse(**response)
