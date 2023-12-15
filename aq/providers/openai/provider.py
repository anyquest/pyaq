import logging
from typing import Dict, Any

from ..provider import BaseProvider, ProviderError
from ...http_client import AsyncHttpClient
from ..types import ChatCompletionRequest, ChatCompletionResponse, Error


class OpenAIProvider(BaseProvider):
    def __init__(self, config: Dict[str, Any], http_client: AsyncHttpClient):
        self._config = config
        self._http_client = http_client
        self._logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def _check_config(config: Dict[str, Any]) -> None:
        required_keys = ['endpoint', 'key']
        if not all(key in config for key in required_keys):
            raise ProviderError("The OpenAI provider is not configured. Add settings to config.yml.")

    async def create_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        self._check_config(self._config)

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._config['key']}"
        }
        url = self._http_client.urljoin(self._config["endpoint"], "/chat/completions")
        response = await self._http_client.post(url, headers, request.model_dump_json(exclude_none=True))

        if "error" in response:
            error = Error(**response['error'])
            raise ProviderError(error.code, error.message)
        else:
            return ChatCompletionResponse(**response)
