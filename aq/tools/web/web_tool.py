import logging
from typing import Dict, Any, List

from bs4 import BeautifulSoup
from pydantic import BaseModel

from ..tool import BaseTool, ToolError
from ...http_client import AsyncHttpClient
from ...providers.types import Tool
from ...types import ToolDef


class SearchResult(BaseModel):
    title: str
    snippet: str
    link: str


class SearchResponse(BaseModel):
    items: List[SearchResult]


class WebTool(BaseTool):
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"

    def __init__(self, config: Dict[str, Any], http_client: AsyncHttpClient):
        self._config = config
        self._http_client = http_client
        self._logger = logging.getLogger(self.__class__.__name__)

    async def get_metadata(self, tool_def: ToolDef) -> List[Tool]:
        return [
            Tool(**{
                "function": {
                    "name": "search",
                    "description": "Searches the Internet and returns a list of matching web pages.",
                    "parameters": {
                        "required": ["query"],
                        "properties": {
                            "query": {
                                "description": "A search expression."
                            }
                        }
                    }
                }
            }),
            Tool(**{
                "function": {
                    "name": "summarize",
                    "description": "Summarizes the contents of a web page.",
                    "parameters": {
                        "required": ["link"],
                        "properties": {
                            "link": {
                                "description": "A universal resource locator (URL) pointing to a web page."
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
            response = await self.search(arguments["query"])
            return response.model_dump_json()
        elif function_name == "summarize":
            if "link" not in arguments:
                raise ToolError("The link argument is required for summarize")
            return await self.summarize(arguments["link"])
        else:
            raise ToolError(f"Unknown function {function_name}")

    async def search(self, query: str) -> SearchResponse:
        self._logger.debug(f"query = {query}")
        try:
            response = await self._http_client.get(self._config["endpoint"], {
                "cx": self._config["cx"],
                "key": self._config["key"],
                "q": query
            }, {
                "Accept": "application/json",
            })
            return SearchResponse(**response)
        except Exception as e:
            self._logger.error(f"Searched failed with error: {e}")

    async def summarize(self, link: str) -> str:
        self._logger.debug(f"link = {link}")

        if not link.startswith(("http://", "https://")):
            link = 'https://' + link.strip("/")

        html = await self._http_client.get(link, {}, {
            "User-Agent": self.USER_AGENT
        }, json=False)

        soup = BeautifulSoup(html, features="html.parser")
        text = soup.get_text()

        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text
