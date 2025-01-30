import dataclasses
from typing import Optional

from pydantic import BaseModel, Field


class UploadSchema(BaseModel):
    phone_number: str = Field(title="Номер телефона без + для доступа в аккаунт", max_length=12)
    access_token: str = Field(title="Токен для доступа в аккаунт")
    refresh_token: str = Field(title="Токен для восстановления access")
    promo_code: str = Field(title="Промокод для активации")
    fake_points: Optional[float] = Field(default=0.0)
    ya_token: str = Field(title='Яндекс токен для подписки')
    fake_free_rides: Optional[int] = Field(default=0)
    account_functionality: Optional[int] = Field(default=0)


@dataclasses.dataclass
class ResponseUploadAccount:
    coupon: str