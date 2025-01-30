import random
import string

from api.default import BaseRequest
from .models import MyTariffsList, TariffList, ActivationResponse


class MtsAPI(BaseRequest):
    def __init__(self, ya_token: str, base_url='https://music.mts.ru/ya_payclick'):
        headers = {'Authorization': f'OAuth {ya_token}'}

        super().__init__(base_url=base_url, headers=headers, debug=True)

    async def get_tariff_now(self, phone_number: str) -> MyTariffsList:
        params = {"msisdn": phone_number}
        response = await self._get(endpoint='subscriptions', params=params)
        return MyTariffsList.model_validate_json(response.text)

    async def get_tariff_list(self, phone_number: str) -> TariffList:
        params = {"msisdn": phone_number}
        response = await self._get(endpoint='content-provider/available-subscriptions', params=params)
        return TariffList.model_validate_json(response.text)

    async def activate_mts_premium(self, phone_number: str, content_id: str) -> ActivationResponse:
        uid = self._generate_uid()
        bid = self._generate_bid()
        json_data = {
            "userId": f"00000000100090099{uid}",
            "bindingId": f"88b32A591b86Dbcaa98b{bid}",
            "msisdn": phone_number,
            "contentId": content_id
        }
        response = await self._post(endpoint='subscriptions', json=json_data)
        try:
            return ActivationResponse.model_validate_json(response.text)
        except Exception as e:
            return ActivationResponse(subscriptionId=None)

    @staticmethod
    def _generate_uid():
        return ''.join(random.choice(string.digits) for _ in range(3))

    @staticmethod
    def _generate_bid():
        return ''.join(random.choice(string.hexdigits) for _ in range(12))
