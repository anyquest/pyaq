from .web import WebTool
from .rest import RestTool
from .tool import BaseTool
from ..types import ToolType


class ToolManager:
    def __init__(self, web_tool: WebTool, rest_tool: RestTool):
        self._tools = {
            ToolType.WEB: web_tool,
            ToolType.REST: rest_tool
        }

    def get_tool(self, tool_type: ToolType) -> BaseTool:
        return self._tools.get(tool_type, None)
