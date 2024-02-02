import logging
import time
import tiktoken
import asyncio
from typing import Dict, Any

from ..provider import BaseProvider, ProviderError
from ...http_client import AsyncHttpClient
from ..types import ChatCompletionRequest, ChatCompletionResponse, Error


class ModelLimits:
    def __init__(self, requests_per_minute: int = 0, tokens_per_minute: int = 0):
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.last_update_time = time.time()
        self.available_request_capacity = self.requests_per_minute
        self.available_token_capacity = self.tokens_per_minute

    def update_capacity(self):
        current_time = time.time()
        seconds_since_update = current_time - self.last_update_time
        self.available_request_capacity = min(self.available_request_capacity +
                                              self.requests_per_minute * seconds_since_update / 60.0,
                                              self.requests_per_minute)
        self.available_token_capacity = min(self.available_token_capacity +
                                            self.tokens_per_minute * seconds_since_update / 60.0,
                                            self.tokens_per_minute)
        self.last_update_time = time.time()

    def consume(self, tokens: int) -> bool:
        self.update_capacity()
        if tokens < self.available_token_capacity and self.available_request_capacity > 1:
            self.available_token_capacity -= tokens
            self.available_request_capacity -= 1
            return True
        else:
            return False


class OpenAIProvider(BaseProvider):

    def __init__(self, config: Dict[str, Any], http_client: AsyncHttpClient):
        self._config = config
        self._http_client = http_client
        self._logger = logging.getLogger(self.__class__.__name__)
        self._encoding = tiktoken.get_encoding("cl100k_base")
        self._limits = ModelLimits(requests_per_minute=5000, tokens_per_minute=160000)

    @staticmethod
    def _check_config(config: Dict[str, Any]) -> None:
        required_keys = ['endpoint', 'key']
        if not all(key in config for key in required_keys):
            raise ProviderError(400, "The OpenAI provider is not configured. Add settings to config.yml.")

    async def create_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        self._check_config(self._config)

        attempts = 360
        tokens = self.estimate_tokens(request)        
        while attempts > 0:
            if self._limits.consume(tokens):
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
            else:
                if tokens >= self._limits.tokens_per_minute:
                    raise ProviderError(400, "Request exceeds maximum token limit")
                
                attempts -= 1
                sleep_time = 10
                self._logger.debug(f"Insufficient token or request capacity. Sleeping {sleep_time} seconds")
                self._logger.debug(f"Estimated tokens: {tokens}. "
                                   f"Available tokens: {self._limits.available_token_capacity}")
                await asyncio.sleep(sleep_time)

    def estimate_tokens(self, request: ChatCompletionRequest) -> int:
        text_list = [message.content for message in request.messages if isinstance(message.content, str)]
        text_list.extend(content.text for message in request.messages if isinstance(message.content, list)
                         for content in message.content if content.type == "text")
        text = "\n".join(text_list)
        num_tokens = len(self._encoding.encode(text))
        return num_tokens + 4096
