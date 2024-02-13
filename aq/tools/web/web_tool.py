import logging
import tiktoken
import asyncio

from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from pydantic import BaseModel

from ...http_client import AsyncHttpClient
from ...providers.types import Tool
from ...types import ToolDef
from ..tool import BaseTool, ToolError


class SearchResult(BaseModel):
    title: str
    snippets: List[str]
    description: str
    url: str

class SearchResponse(BaseModel):
    hits: Optional[List[SearchResult]] = None


class WebTool(BaseTool):
    USER_AGENT = "Mozilla/5.0"

    def __init__(self, config: Dict[str, Any], http_client: AsyncHttpClient):
        self._config = config
        self._http_client = http_client
        self._logger = logging.getLogger(self.__class__.__name__)
        self._encoding = tiktoken.get_encoding("cl100k_base")


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
            response = await self.search(arguments, tool_def)
            return response.model_dump_json()
        elif function_name == "summarize":
            if "link" not in arguments:
                raise ToolError("The link argument is required for summarize")
            return await self.summarize(arguments["link"], tool_def)
        else:
            raise ToolError(f"Unknown function {function_name}")

    async def search(self, arguments: Dict[str, Any], tool_def: ToolDef) -> SearchResponse:
        query = arguments["query"]
        num_results = tool_def.parameters.get("results", 3)
        self._logger.debug(f"query = {query}, results={num_results}")
        try:
            retry_count = 0
            while retry_count < 3:
                response = await self._http_client.get(self._config["endpoint"], {
                    "query": query,
                    "num_web_results": num_results
                }, {
                    "Accept": "application/json",
                    "X-API-Key": self._config["key"]
                })

                search_response = SearchResponse(**response)
                if not search_response.hits:
                    self._logger.debug("Search produced no results. Retrying ...")
                    retry_count += 1
                    await asyncio.sleep(5*(2**retry_count))

                return search_response

        except Exception as e:
            self._logger.error(f"Web search failed with error: {e}")
            return SearchResponse()

    async def summarize(self, link: str, tool_def: ToolDef) -> str:
        self._logger.debug(f"link = {link}")

        max_tokens = tool_def.parameters.get("max_tokens", 1000)
        max_characters = max_tokens * 4

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
        if len(text) > max_characters:
            text = text[:max_characters] + "..."

        return text
