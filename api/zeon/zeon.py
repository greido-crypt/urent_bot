from io import BytesIO

import aiohttp

from ..default import BaseRequest, BaseRequestModel


class ZeonAPI(BaseRequest):
    def __init__(self, port: int, debug: bool = False):
        self.base_url = f'https://zeon-shop.ru:{port}'
        super().__init__(self.base_url, timeout=10, debug=debug)

    async def urent_payment_create_mir(self,
                                       payment_url: str,
                                       methodData: str,
                                       methodUrl: str,
                                       orderN: str) -> BaseRequestModel:
        json_data = {"payment_url": f"{payment_url}",
                     "methodData": f"{methodData}",
                     "methodUrl": f"{methodUrl}",
                     "orderN": f"{orderN}"}
        return await self._post(endpoint='urent/payment/create/mir', json=json_data)

    async def urent_payment_create_visa(self,
                                        payment_url: str,
                                        pa_req: str,
                                        md: str,
                                        term_url: str) -> BaseRequestModel:
        json_data = {"payment_url": f"{payment_url}",
                     "pa_req": f"{pa_req}",
                     "md": f"{md}",
                     "term_url": f"{term_url}"}
        return await self._post(endpoint='urent/payment/create/visa', json=json_data)

    async def urent_payment_create_ecom_creq_mir(self,
                                                 payment_url: str,
                                                 creq: str):
        json_data = {
            "payment_url": payment_url,
            "creq": creq
        }

        return await self._post(endpoint="urent/payment/create/ecom/creq/mir", json=json_data)

    async def urent_payment_create_ecom_mir(self, payment_url: str, creq: str):
        json_data = {
            "payment_url": payment_url,
            "creq": creq
        }
        return await self._post(endpoint="urent/payment/create/ecom/mir", json=json_data)

    async def urent_send_html_rides(self, phone_number: int | str, html_file: BytesIO):
        file_send = aiohttp.FormData()
        file_send.add_field('file', html_file, filename=f'{phone_number}.html')
        await self._post(endpoint='upload', data=file_send)
        return f"{self.base_url}/view/{phone_number}.html"
