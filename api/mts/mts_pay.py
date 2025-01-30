import json
import uuid

import aiohttp
from bs4 import BeautifulSoup

from api.default import BaseRequest


class MtsPay(BaseRequest):
    def __init__(self, session_id: str, debug: bool = False):
        self._base_url = 'https://pay.mts.ru'
        self.__session_id = session_id
        self.__request_id = str(uuid.uuid4())
        self._headers = {
            "Session-Id": self.__session_id,
            "Request-Id": self.__request_id
        }
        super().__init__(self._base_url, debug=debug)

    def __call__(self, *args, **kwargs):
        if self._headers.get('Request-Id'):
            self.__request_id = str(uuid.uuid4())
            self._headers.update({'Request-Id': self.__request_id})

    async def _paymentInfo(self, ssoTokenId: str):
        json_data = {'ssoTokenId': ssoTokenId}
        response = await self._post(endpoint='api/public/v1.2/payment/info', json=json_data)
        getDSMethodData: dict = json.loads(response.text)
        return getDSMethodData

    async def _paymentProcess(self, card_info: dict):
        json_data = {
            "paymentTool": {
                "card": {
                    "cvc": f"{card_info['cvv']}",
                    "expiryMonth": f"{card_info['month']}",
                    "expiryYear": f"20{card_info['year']}",
                    "needSaveCard": "false",
                    "number": f"{card_info['card_number']}"
                },
                "type": "NEW_CARD"
            }
        }
        response = await self._post(endpoint='api/public/v1.2/payment/process', json=json_data)
        getDSMethodData: dict = json.loads(response.text)
        return getDSMethodData

    async def _paymentProceed(self):
        data = {
            "browserJavascriptEnabled": "true",
            "browserLanguage": "ru",
            "threeDsRequestorUrl": "https://pay.mts.ru"
        }
        self._base_url = 'https://pay.mts.ru'
        self._headers = {
            "User-Agent": "IE 5.0",
            "Requestor-Name": "ru.urentbike.app 1.53.1",
            "Session-Id": self.__session_id,
            "Request-Id": self.__request_id
        }
        response = await self._post(endpoint='api/public/v1.2/payment/3ds2/proceed', json=data)
        json_response = json.loads(response.text)
        json_response: dict
        return json_response

    async def _confirmPayment(self):
        json_data = {
            "confirmInput": {
                "3ds2": ""
            }
        }
        response = await self._post(endpoint='api/public/v1.2/payment/confirm', json=json_data)
        getDSMethodData: dict = json.loads(response.text)
        return getDSMethodData

    async def _deleteBindings(self, cardId: str, ssoTokenId: str):
        json_data = {
            "id": cardId,
            "ssoTokenId": ssoTokenId
        }
        response = await self._post(endpoint='api/public/v1.1/service/ewallet/bindings/delete', json=json_data)


    async def _bindingsEWallet(self, ssoTokenId: str):
        del self._headers['Session-Id']
        json_data = {
            "ssoTokenId": ssoTokenId
        }
        response = await self._post(endpoint='api/public/v1.1/service/ewallet/bindings', json=json_data)
        getCardList: dict = json.loads(response.text)
        return getCardList

    async def createPayment(self, ssoTokenId: str):
        response = await self._paymentInfo(ssoTokenId=ssoTokenId)
        response = await self._paymentProcess()
        if response['confirm']['tool'].get('card3ds'):
            pa_req = response['confirm']['tool']['card3ds']['paReq']
            url = response['confirm']['tool']['card3ds']['acsUrl']
            term_url = response['confirm']['tool']['card3ds']['termUrl']
            jsonVisa = {
                "PaReq": pa_req,
                "MD": "any",
                "url": url,
                "TermUrl": term_url
            }
            return jsonVisa

        threeDSMethodData = response['confirm']['tool']['card3ds2']['threeDsMethodData']
        termUrl = response['confirm']['tool']['card3ds2']['threeDsMethodUrl']
        data = {
            "threeDSMethodData": threeDSMethodData
        }
        self._base_url = termUrl
        # self._headers = {}
        response = await self._post(endpoint='', json=data, verify_ssl=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        notification_url = soup.find('form', {'id': 'callbackForm'}).get('action')
        print("notification_url", notification_url)
        threeDSMethodData = soup.find('input', {'id': 'threeDSMethodData'}).get('value')
        print("threeDSMethodData", threeDSMethodData)
        data = {
            'threeDSMethodData': threeDSMethodData
        }
        self._base_url = notification_url
        response = await self._post(endpoint='', json=data, verify_ssl=False)
        # getDSMethodData: dict = json.loads(response.text)
        response = await self._paymentProceed()
        return response

    async def checkPayment(self):
        response = await self._confirmPayment()
