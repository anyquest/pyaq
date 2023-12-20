import logging
from typing import Dict, Any
from urllib.parse import urlencode

import httpx
import asyncio


class AsyncHttpClient:
    TIMEOUT = 120

    def __init__(self):
        logging.getLogger('httpcore').setLevel(logging.ERROR)
        logging.getLogger('httpx').setLevel(logging.ERROR)
        self._logger = logging.getLogger(self.__class__.__name__)

    async def post(self, url: str, headers: Dict[str, Any], data: Any, json=True) -> Any:
        retry_count = 0
        while retry_count < 5:
            try:
                async with httpx.AsyncClient() as ac:
                    response = await ac.post(url, headers=headers, data=data, timeout=self.TIMEOUT)
                if json:
                    json_response = response.json()
                    if "error" in json_response and "code" in json_response["error"]:
                        code = int(json_response["error"]["code"])
                        if code == 429:
                            self._logger.error("Received a 429 error. Retrying ...")
                            retry_count += 1
                            await asyncio.sleep(5*(2**retry_count))
                        else:
                            return json_response
                    else:
                        return json_response
                else:
                    return response.text
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    self._logger.error("Received a 429 error. Retrying ...")
                    retry_count += 1
                    await asyncio.sleep(5*(2**retry_count))
                else:
                    self._logger.error(f"HTTP error: {e.response.status_code}, {e.response.text}")
                    raise e

    async def get(self, url: str, query: Dict[str, Any] = None, headers: [str, Any] = None, json=True) -> Any:
        get_url = f"{url}?{urlencode(query)}" if query else url
        async with httpx.AsyncClient() as ac:
            response = await ac.get(get_url, headers=headers or {}, timeout=self.TIMEOUT)
        return response.json() if json else response.text

    @staticmethod
    def urljoin(*args):
        stripped = map(lambda x: str(x).strip('/'), args)
        return "/".join(stripped)

