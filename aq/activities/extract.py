import json
import logging
from typing import Dict, Any, List

from .activity import BaseActivity, ActivityError
from ..providers import ProviderManager
from ..providers.types import (
    ChatCompletionMessage,
    ChatCompletionRequest,
    Choice,
    Function,
    Tool
)
from ..types import ActivityJob, JobState


class ExtractActivity(BaseActivity):
    def __init__(self, provider_manager: ProviderManager):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._provider_manager = provider_manager

    async def perform(self, activity_job: ActivityJob, inputs: Dict[str, Any]) -> None:
        try:
            app = activity_job.app_job.app
            activity = app.activities[activity_job.activity_name]

            if len(activity.models) < 1:
                raise ActivityError("A model is required")
            model = app.models[activity.models[0]]

            schema = activity.parameters.get("schema", None)
            if not schema:
                raise ActivityError("A schema is required")
            if not isinstance(schema, list):
                raise ActivityError("A schema must be a list of types")

            tools = []
            for schema_def in schema:
                func_def = Function(**schema_def)
                tools.append(Tool(function=func_def))

            messages = []
            profile = app.info.profile
            if profile:
                messages.append(ChatCompletionMessage(role="system", content=profile))

            messages.append(ChatCompletionMessage(role="system", content="""
                Use the tools provided with information extracted from the user prompt.
                Use the entire prompt as the source of information. Do not exclude or omit anything.
            """))
            messages.append(ChatCompletionMessage(role="user", content=self.merge_inputs(inputs)))

            values: Dict[str, List[Any]] = {}
            provider = self._provider_manager.get_provider(model.provider)
            for x in range(self.MAX_ITERATIONS):
                request = ChatCompletionRequest(
                    model=model.model,
                    messages=messages,
                    temperature=0.0,
                    tools=tools,
                    tool_choice="auto"
                )
                response = await provider.create_completion(request)

                choice: Choice = response.choices[0]
                message: ChatCompletionMessage = choice.message
                messages.append(message)

                if choice.finish_reason == "tool_calls":
                    for tool_call in message.tool_calls:
                        function_call = tool_call.function
                        values_for_type = values.get(function_call.name, None)
                        if not values_for_type:
                            values_for_type = []
                            values[function_call.name] = values_for_type
                        values_for_type.append(json.loads(function_call.arguments))
                        messages.append(ChatCompletionMessage(
                            role="tool",
                            tool_call_id=tool_call.id,
                            name=function_call.name,
                            content="Success"
                        ))
                elif choice.finish_reason:
                    break

            activity_job.state = JobState.SUCCESS
            activity_job.output = json.dumps(values)
            activity_job.output_type = "application/json"

        except Exception as e:
            self._logger.error(e)
            activity_job.state = JobState.ERROR
            activity_job.output = str(e)


