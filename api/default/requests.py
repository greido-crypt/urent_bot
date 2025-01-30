import asyncio
import random

import aiohttp
from aiohttp import ClientConnectorError, ServerDisconnectedError

from loader import bot_logger
from settings import HELPED_PROXY_LIST, CHANNEL_ID
from .models import BaseRequestModel


class BaseRequest(object):
    def __init__(self,
                 base_url: str,
                 headers: dict = None,
                 proxy: str = None,
                 timeout: int = 5,
                 debug: bool = False):
        self._base_url = base_url
        self._headers = headers
        self.__proxy = proxy
        print('[DEBUG] Accepted __proxy:', self.__proxy)
        self.__timeout = timeout
        self.__debug = debug

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> BaseRequestModel:
        url = f"{self._base_url}/{endpoint}" if endpoint != '' else self._base_url
        if self.__debug:
            dict_kwargs = {**kwargs}
            print(f'[DEBUG] Request URL: {url} Params: {dict_kwargs}')
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method=method, url=url, headers=self._headers,
                                           proxy=self.__proxy, timeout=self.__timeout, **kwargs) as response:
                    # response.raise_for_status()
                    if self.__debug:
                        print(f'[DEBUG] Response URL: {url} Response: {await response.text()}')
                    return BaseRequestModel(text=await response.text(encoding="utf-8"), status_code=response.status,
                                            response=response)

        except aiohttp.ClientHttpProxyError:
            try:
                await bot_logger.send_message(chat_id=CHANNEL_ID,
                                              text=f'<b>🚫 Отвалился прокси: {self.__proxy}</b>')
            except Exception as e:
                pass
            self.__proxy = random.choice(HELPED_PROXY_LIST)
            print('[DEBUG] Accepted __proxy:', self.__proxy)
            return await self._make_request(method, endpoint, **kwargs)

        except asyncio.TimeoutError:
            return await self._make_request(method, endpoint, **kwargs)

        except ClientConnectorError:
            return await self._make_request(method, endpoint, **kwargs)

        except ServerDisconnectedError:
            return await self._make_request(method, endpoint, **kwargs)

    async def _get(self, endpoint: str, params=None, **kwargs) -> BaseRequestModel:
        r"""Sends a GET request.
            :param params: (optional) Dictionary, list of tuples or bytes to send
                in the query string for the :class:`Request`.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: :class:`Response <Response>` object
            """
        return await self._make_request(method="GET", endpoint=endpoint, params=params, **kwargs)

    async def _post(self, endpoint: str, **kwargs) -> BaseRequestModel:
        r"""Sends a POST request.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
        object to send in the body of the :class:`Request`.
        :param json: (optional) A JSON serializable Python object to send in the body.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """
        return await self._make_request(method="POST", endpoint=endpoint, **kwargs)

    async def _put(self, endpoint: str, **kwargs) -> BaseRequestModel:
        return await self._make_request(method="PUT", endpoint=endpoint, **kwargs)

    async def _delete(self, endpoint: str, **kwargs) -> BaseRequestModel:
        return await self._make_request(method="DELETE", endpoint=endpoint, **kwargs)
