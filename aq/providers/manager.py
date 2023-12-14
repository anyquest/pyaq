import logging

from .openai import OpenAIProvider
from .azure import AzureProvider
from .anthropic import AnthropicProvider
from .llava import LlavaProvider
from ..types import ModelProvider
from .provider import BaseProvider


class ProviderManager:
    def __init__(self, openai_provider: OpenAIProvider,
                 azure_provider: AzureProvider,
                 anthropic_provider: AnthropicProvider,
                 llava_provider: LlavaProvider):
        self._providers = {
            ModelProvider.OPENAI: openai_provider,
            ModelProvider.AZURE: azure_provider,
            ModelProvider.ANTHROPIC: anthropic_provider,
            ModelProvider.LLAVA: llava_provider
        }
        self._logger = logging.getLogger(self.__class__.__name__)

    def get_provider(self, provider_type: ModelProvider) -> BaseProvider:
        return self._providers[provider_type]

