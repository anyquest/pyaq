import logging
from typing import Dict, Any
from urllib.parse import urlencode

import httpx
from tenacity import retry, stop_after_attempt, wait_random_exponential


class AsyncHttpClient:
    TIMEOUT = 120

    def __init__(self):
        logging.getLogger('httpcore').setLevel(logging.ERROR)
        logging.getLogger('httpx').setLevel(logging.ERROR)

    @retry(stop=stop_after_attempt(5), wait=wait_random_exponential(min=1, max=60))
    async def post(self, url: str, headers: Dict[str, Any], data: Any, json=True) -> Any:
        async with httpx.AsyncClient() as ac:
            response = await ac.post(url, headers=headers, data=data, timeout=self.TIMEOUT)
        return response.json() if json else response.text

    async def get(self, url: str, query: Dict[str, Any] = None, headers: [str, Any] = None, json=True) -> Any:
        get_url = f"{url}?{urlencode(query)}" if query else url
        async with httpx.AsyncClient() as ac:
            response = await ac.get(get_url, headers=headers or {}, timeout=self.TIMEOUT)
        return response.json() if json else response.text

    @staticmethod
    def urljoin(*args):
        stripped = map(lambda x: str(x).strip('/'), args)
        return "/".join(stripped)

