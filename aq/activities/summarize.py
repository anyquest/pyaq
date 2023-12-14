import logging
import time
from typing import Dict, Any

from .activity import BaseActivity, ActivityError
from ..types import ModelProvider, ActivityJob, JobState
from ..providers import ProviderManager
from ..providers.types import ChatCompletionMessage, ChatCompletionRequest, Choice


class SummarizeActivity(BaseActivity):
    def __init__(self, provider_manager: ProviderManager):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._provider_manager = provider_manager

    async def perform(self, activity_job: ActivityJob, inputs: Dict[str, Any]) -> None:
        try:
            app = activity_job.app_job.app
            activity = app.activities[activity_job.activity_name]

            # Get the text for summarization
            text = self.merge_inputs(inputs)
            if not text:
                raise ActivityError(f"Text is required")

            # Get the model
            if len(activity.models) < 1:
                raise ActivityError(f"A model is required")
            model = app.models[activity.models[0]]

            # Get the model parameters
            sentences = int(activity.parameters.get("sentences", model.parameters.get("sentences", 10)))
            temperature = float(activity.parameters.get("temperature", model.parameters.get("temperature", 0.5)))

            summary = await self.summarize(app.info.profile, text, model.provider,
                                           model.model, sentences, temperature)

            activity_job.output = summary
            activity_job.state = JobState.SUCCESS
            activity_job.output_type = "text/markdown"

        except Exception as e:
            activity_job.state = JobState.ERROR
            activity_job.output = str(e)
            self._logger.error(f"Encountered an error {e}")

    async def summarize(self, context: str, text: str,
                        provider_type: ModelProvider, model: str,
                        sentences: int, temperature: float) -> str:
        messages = []
        if context:
            messages.append(ChatCompletionMessage(role="system", content=context))

        prompt = """
            Summarize a block of text provided inside triple back ticks.
            Your summary must be readable. 
            Your summary must include about %(sentences)d sentences.
            ```%(text)s```
        """
        prompt = prompt % {"text": text, "sentences": sentences}
        messages.append(ChatCompletionMessage(role="user", content=prompt))

        request = ChatCompletionRequest(
            model=model,
            messages=messages,
            temperature=temperature
        )
        provider = self._provider_manager.get_provider(provider_type)

        start_time = time.perf_counter()

        response = await provider.create_completion(request)
        choice: Choice = response.choices[0]
        message: ChatCompletionMessage = choice.message

        self._logger.debug(f"Finished with reason {choice.finish_reason} "
                           f"in {int(time.perf_counter()-start_time)} sec.")

        return message.content
