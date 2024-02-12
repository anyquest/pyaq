import logging
from typing import Any, Dict, List

from bs4 import BeautifulSoup
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
                            }
                        }
                    }
                }
            }),
            Tool(**{
                "function": {
                    "name": "summarize",
                    "description": "Summarizes a news story.",
                    "parameters": {
                        "required": ["link"],
                        "properties": {
                            "link": {
                                "description": "A universal resource locator (URL) pointing to a news story."
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
        elif function_name == "summarize":
            if "link" not in arguments:
                raise ToolError("The link argument is required for summarize")
            return await self.summarize(arguments["link"])
        else:
            raise ToolError(f"Unknown function {function_name}")

    async def search(self, arguments: Dict[str, Any]) -> NewsResponse:
        query = arguments["query"]
        self._logger.debug(f"query = {query}")
        try:
            response = await self._http_client.get(self._config["endpoint"], {
                "q": query
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
        if len(text) > 2000:
            text = text[:2000] + "..."

        return text
