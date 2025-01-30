import json
import random

from settings import PROXY_LIST
from .models import PostData, RequestDataModel
from ..default import BaseRequest


class VpsKotAPI(BaseRequest):
    def __init__(self):
        self.base_url = f'http://95.216.45.87:8000'
        super().__init__(self.base_url,
                         timeout=3,
                         proxy=random.choice(PROXY_LIST))

    async def request_data(self, post_data: PostData):
        response = await self._post(endpoint='request_data/', json=json.loads(post_data.model_dump_json()))
        return RequestDataModel.RequestData.model_validate_json(response.text)
