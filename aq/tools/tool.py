from typing import List, Dict, Any

from ..providers.types import Tool
from ..types import ToolDef


class ToolError(Exception):
    pass


class BaseTool:
    async def get_metadata(self, tool_def: ToolDef) -> List[Tool]:
        pass

    async def invoke(self, function_name: str, arguments: Dict[str, Any], tool_def: ToolDef) -> str:
        pass
