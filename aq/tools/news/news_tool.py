import logging
from typing import Any, Dict, List

from pydantic import BaseModel

from ..tool import BaseTool, ToolError
from ...http_client import AsyncHttpClient
from ...providers.types import Tool
from ...types import ToolDef


class NewsResult(BaseModel):
    age: str
    description: str
    title: str
    url: str


class NewsResults(BaseModel):
    results: List[NewsResult]


class NewsResponse(BaseModel):
    news: NewsResults


class NewsTool(BaseTool):
    USER_AGENT = "Mozilla/5.0"

    def __init__(self, config: Dict[str, Any], http_client: AsyncHttpClient):
        self._config = config
        self._http_client = http_client
        self._logger = logging.getLogger(self.__class__.__name__)

    async def get_metadata(self, tool_def: ToolDef) -> List[Tool]:
        return [
            Tool(**{
                "function": {
                    "name": "search",
                    "description": "Searches the news stream and returns a list of matching news stories.",
                    "parameters": {
                        "required": ["query"],
                        "properties": {
                            "query": {
                                "description": "A news search expression."
                            },
                            "count": {
                                "description": "The max number of web results to return, must be under 20."
                            },
                            "offset": {
                                "description": "The offset, in multiples of count. I.e if count = 5, and offset=1, the API will return results 5-10. The maximum value for offset is 9."
                            }
                        }
                    }
                }
            })
        ]

    async def invoke(self, function_name: str, arguments: Dict[str, Any], tool_def: ToolDef) -> str:
        if function_name == "search":
            if "query" not in arguments:
                raise ToolError("The query argument is required for search")
            response = await self.search(arguments)
            return response.model_dump_json()
        else:
            raise ToolError(f"Unknown function {function_name}")

    async def search(self, arguments: Dict[str, Any]) -> NewsResponse:
        query = arguments["query"]
        count = arguments.get("count", 20)
        offset = arguments.get("offset", 0)
        self._logger.debug(f"query = {query}, count={count}, offset={offset}")
        try:
            response = await self._http_client.get(self._config["endpoint"], {
                "q": query,
                "count": count,
                "offset": offset
            }, {
               "Accept": "application/json",
               "X-API-Key": self._config["key"]
            })

            news_response = NewsResponse(**response)
            if not news_response.news.results:
                self._logger.debug("News search produced no results")

            return news_response
        except Exception as e:
            self._logger.error(f"News search failed with error: {e}")
            return NewsResponse()

