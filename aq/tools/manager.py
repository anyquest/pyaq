from .web import WebTool
from .rest import RestTool
from .news import NewsTool
from .tool import BaseTool
from ..types import ToolType


class ToolManager:
    def __init__(self, web_tool: WebTool, rest_tool: RestTool, news_tool: NewsTool):
        self._tools = {
            ToolType.WEB: web_tool,
            ToolType.REST: rest_tool,
            ToolType.NEWS: news_tool
        }

    def get_tool(self, tool_type: ToolType) -> BaseTool:
        return self._tools.get(tool_type, None)
