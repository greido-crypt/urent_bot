from typing import List, Optional

from pydantic import BaseModel, RootModel


class BaseRequestModel(BaseModel):
    text: str
    status_code: int


class MyTariff(BaseModel):
    subscriptionId: str
    contentId: str
    price: float
    period: int
    isPremiumSubscriber: bool
    isMtsSubscriber: bool
    subscriptionDate: str
    tarifficationStatus: int
    contentName: str


class MyTariffsList(RootModel):
    root: List[MyTariff]


class Tariff(BaseModel):
    contentId: str
    contentName: str
    period: int
    trialPeriod: int
    price: float
    isTrial: bool


class TariffList(RootModel):
    root: List[Tariff]


class ActivationResponse(BaseModel):
    subscriptionId: Optional[str] = None


class InviteModel:
    class Invite(BaseModel):
        id: int
        userID: int
        sponsorMsisdn: str
        msisdn: int
        code: str
        status: int
        reason: int
        expiredAt: str
        createdAt: str

    class Model(BaseModel):
        Invite: 'InviteModel.Invite'
        NewStatus: str
        NewReason: str
        link: str


class AuthModel(BaseModel):
    phone_number: str
    state: str
    sms_code: str = None
