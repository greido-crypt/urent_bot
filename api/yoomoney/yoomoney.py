import json
import random

from api.default import BaseRequest, BaseRequestModel
from api.urent.models import PaymentStatus, CardForPaymentModel
from settings import PROXY_LIST


class YooMoneyAPI(BaseRequest):
    def __init__(self):
        self._base_url = 'https://yoomoney.ru'
        super().__init__(self._base_url, debug=True, proxy=random.choice(PROXY_LIST))

    async def getMirPayPaymentLink(self, order_id: str | int) -> str:
        params = {"orderId": order_id}
        response = await self._get(endpoint='checkout/payments/v2/mir-pay/payment-link', params=params)
        response_json = json.loads(response.text)
        payment_link = response_json['payload']['paymentLink']
        payment_link: str = payment_link.replace("intent", "https", 1)
        return payment_link

    async def anyCardStart(self, orderId: str, cardSynonym: str, sk: str) -> BaseRequestModel:
        json_data = {"orderId": orderId, "cardSynonym": cardSynonym, "sk": sk}
        self._headers = {}
        self._base_url = 'https://yoomoney.ru'
        response = await self._post(endpoint='checkout/payments/v2/payment/anycard/start', json=json_data)
        return response

    async def paymentStatus(self, orderId: str, sk: str) -> PaymentStatus:
        json_data = {"orderId": f"{orderId}", "sk": f"{sk}"}
        self._headers = {}
        response = await self._post(endpoint='checkout/payments/v2/payment/status', json=json_data)
        return PaymentStatus.model_validate_json(response.text)

    async def yoomoneyStoreCardForPayment(self,
                                          pan: int | str,
                                          expireDate: int | str,
                                          csc: int | str,
                                          requestId: int | str,
                                          ):
        """
        pan: card_number
        expireDate: 202409: 20 + year + month
        csc: cvc
        requestId: order_id
        """
        json_data = {"cardholder": "CARD HOLDER", "pan": f"{pan}", "expireDate": f"{expireDate}", "csc": f"{csc}",
                     "requestId": f"{requestId}"}
        self._base_url = 'https://paymentcard.yoomoney.ru'
        response = await self._post(endpoint='webservice/storecard/api/storeCardForPayment', json=json_data)
        return CardForPaymentModel.CardForPayment.model_validate_json(response.text)
