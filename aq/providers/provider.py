from .types import ChatCompletionRequest, ChatCompletionResponse


class ProviderError(Exception):
    pass


class BaseProvider:
    async def create_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        pass
