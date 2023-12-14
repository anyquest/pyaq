import logging
from typing import Dict, Any, List

from openapi_parser import parse
from openapi_parser.enumeration import OperationMethod

from ..tool import BaseTool, ToolError
from ...http_client import AsyncHttpClient
from ...providers.types import Tool
from ...types import ToolDef


class RestTool(BaseTool):
    def __init__(self, http_client: AsyncHttpClient):
        self._http_client = http_client
        logging.getLogger('openapi_parser').setLevel(logging.ERROR)
        self._logger = logging.getLogger(self.__class__.__name__)

    async def get_metadata(self, tool_def: ToolDef) -> List[Tool]:
        params = tool_def.parameters or {}
        endpoint = params.get("endpoint", None)
        if not endpoint:
            raise ToolError(f"An REST service endpoint is required")

        openapi_url = params.get("openapi", self._http_client.urljoin(endpoint, "openapi.json"))
        try:
            tools = []
            data = await self._http_client.get(openapi_url)
            spec = parse(spec_string=data)
            for path in spec.paths:
                for operation in path.operations:
                    if operation.method == OperationMethod.GET:
                        required = []
                        props = {}
                        for parameter in operation.parameters:
                            if parameter.required:
                                required.append(parameter.name)
                            props[parameter.name] = {
                                "type": parameter.schema.type.value,
                                "description": parameter.description
                            }
                        path_steps = path.url.split("/")
                        tool = {
                            "function": {
                                "name": path_steps[1],
                                "description": operation.description,
                                "parameters": {
                                    "properties": props,
                                    "required": required
                                }
                            }
                        }
                        tools.append(Tool(**tool))
            return tools
        except Exception as e:
            self._logger.error(f"Failed to get REST metadata {e}")

    async def invoke(self, function_name: str, arguments: Dict[str, Any], tool_def: ToolDef) -> str:
        params = tool_def.parameters or {}
        endpoint = params.get("endpoint", None)
        if not endpoint:
            raise ToolError(f"An REST service endpoint is required")

        url = self._http_client.urljoin(endpoint, function_name)
        return await self._http_client.get(url, arguments, headers={}, json=False)


