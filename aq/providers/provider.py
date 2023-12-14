from .types import ChatCompletionRequest, ChatCompletionResponse


class BaseProvider:
    async def create_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        pass
