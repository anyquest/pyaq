from .types import ChatCompletionRequest, ChatCompletionResponse


class ProviderError(Exception):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


class BaseProvider:
    async def create_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        pass