import json
import logging
import time
from typing import Dict, Any, List

from .activity import BaseActivity, ActivityError
from ..providers import ProviderManager
from ..providers.types import ChatCompletionMessage, ChatCompletionRequest, Choice, Tool, ResponseFormat, ToolCall
from ..tools import ToolManager
from ..types import ActivityJob, JobState, Activity, App


class GenerateActivity(BaseActivity):
    TOOL_NAME_DELIMITER = "__"

    def __init__(self, provider_manager: ProviderManager, tool_manager: ToolManager):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._provider_manager = provider_manager
        self._tool_manager = tool_manager

    async def perform(self, activity_job: ActivityJob, inputs: Dict[str, Any]) -> None:
        try:
            app = activity_job.app_job.app
            activity = app.activities[activity_job.activity_name]

            if len(activity.models) < 1:
                raise ActivityError(f"A model is required")
            model = app.models[activity.models[0]]

            temperature = float(activity.parameters.get("temperature", model.parameters.get("temperature", 0.5)))
            max_tokens = int(activity.parameters.get("max_words", model.parameters.get("max_words", 500))*4/3)

            messages = []
            profile = app.info.profile
            if profile:
                messages.append(ChatCompletionMessage(role="system", content=profile))

            json_format = activity.parameters.get("format", None) == "json"
            if json_format:
                messages.append(ChatCompletionMessage(
                    role="system",
                    content="Provide your response as a JSON object."))
            else:
                messages.append(ChatCompletionMessage(
                    role="system",
                    content="Use the tab length of two spaces when formatting nested lists in markdown."))

            tools = await self.get_tools(app, activity)
            if tools:
                messages.append(ChatCompletionMessage(
                    role="system",
                    content="Think step-by-step. Perform as many iterations as necessary "
                            "to accomplish your goal using the tools provided."))

            prompt_template = activity.parameters["prompt"]
            prompt = self.render(prompt_template, inputs)
            messages.append(ChatCompletionMessage(role="user", content=prompt))

            parts = []
            start_time = time.perf_counter()
            provider = self._provider_manager.get_provider(model.provider)
            for x in range(self.MAX_ITERATIONS):
                request = ChatCompletionRequest(
                    model=model.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools if tools else None,
                    tool_choice="auto" if tools else None,
                    response_format=ResponseFormat(type="json_object") if json_format else None
                )

                response = await provider.create_completion(request)

                choice: Choice = response.choices[0]
                message: ChatCompletionMessage = choice.message
                messages.append(message)

                if choice.finish_reason == "tool_calls":
                    for tool_call in message.tool_calls:
                        tool_result = await self.process_tool_call(tool_call, app)
                        messages.append(tool_result)
                else:
                    if message.content:
                        parts.append(message.content)
                    if choice.finish_reason:
                        self._logger.debug(f"Finished with reason {choice.finish_reason} "
                                           f"in {int(time.perf_counter()-start_time)} sec.")
                        break

            activity_job.state = JobState.SUCCESS
            activity_job.output = "\n\n".join(parts)
            activity_job.output_type = "text/markdown"

        except Exception as e:
            self._logger.error(e)
            activity_job.state = JobState.ERROR
            activity_job.output = str(e)

    async def get_tools(self, app: App, activity: Activity) -> List[Tool]:
        tools = []
        if activity.tools:
            for tool_name in activity.tools:
                tool_def = app.tools[tool_name]
                tool_obj = self._tool_manager.get_tool(tool_def.type)
                metadata = await tool_obj.get_metadata(tool_def)
                for tool in metadata:
                    func = tool.function
                    func.name = f"{tool_name}{self.TOOL_NAME_DELIMITER}{func.name}"
                    tools.append(tool)
        return tools

    async def process_tool_call(self, tool_call: ToolCall, app: App) -> ChatCompletionMessage:
        self._logger.debug(f"Calling {tool_call.function.name}")

        names = tool_call.function.name.split(self.TOOL_NAME_DELIMITER)
        if len(names) < 2:
            raise ActivityError(f"Invalid tool name {tool_call.function.name}")

        if names[0] not in app.tools:
            raise ActivityError(f"{names[0]} is not a valid tool name")

        tool_def = app.tools[names[0]]
        tool_obj = self._tool_manager.get_tool(tool_def.type)

        arguments = json.loads(tool_call.function.arguments)
        response = await tool_obj.invoke(names[1], arguments, tool_def)

        return ChatCompletionMessage(
            role="tool",
            tool_call_id=tool_call.id,
            name=tool_call.function.name,
            content=response
        )
