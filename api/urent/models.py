from typing import List, Any, Optional

from pydantic import BaseModel, Field


class JWTHeader(BaseModel):
    alg: str
    kid: str
    typ: str
    x5t: str


class JWTPayload(BaseModel):
    phone_number: str


class TokenStatus(BaseModel):
    wrong_refresh_token: bool = False


class Error(BaseModel):
    key: str
    value: List[str]


class CardsDelete:
    class Error(BaseModel):
        value: List[str]

    class Model(TokenStatus):
        errors: List['CardsDelete.Error']


class CardsModel:
    class Entry(BaseModel):
        cardNumber: str
        id: str

    class Cards(BaseModel):
        entries: List['CardsModel.Entry'] = []
        errors: List[Error] = []
        succeeded: bool


class ProfileModel:
    class PassportImage(BaseModel):
        path: Any
        type: str
        isGood: bool

    class Statistics(BaseModel):
        distance: float
        kcal: float
        elapsedSeconds: float
        tripCount: int

    class Profile(TokenStatus):
        phoneNumber: str
        id: str
        statistics: 'ProfileModel.Statistics'
        passportImages: List['ProfileModel.PassportImage'] = []
        lastOrderZoneName: Any
        notification: Any
        errors: List[Error] = []
        succeeded: bool


class ConnectToken(BaseModel):
    access_token: str
    refresh_token: str


class PaymentProfileModel:
    class Amount(BaseModel):
        value: float = None
        valueFormatted: str = None

    class LastPurchase(BaseModel):
        amount: Optional['PaymentProfileModel.Amount'] = None
        dateTimeUtc: Optional[str] = None

    class Deposit(BaseModel):
        culture: str
        value: float
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class Bonuses(BaseModel):
        culture: str
        value: float
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class Bonus(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class PromoCode(BaseModel):
        code: str
        bonus: Optional['PaymentProfileModel.Bonus']

    class PaymentProfile(TokenStatus):
        bonuses: 'PaymentProfileModel.Bonuses'
        deposit: 'PaymentProfileModel.Deposit'
        cards: List
        promoCode: str
        promoCodes: List['PaymentProfileModel.PromoCode'] = []
        lastPurchase: 'PaymentProfileModel.LastPurchase'
        errors: List[Error]


class ActivityModel:
    class BonusWithdrawnMoney(BaseModel):
        valueFormattedWithoutZero: str

    class Charge(BaseModel):
        batteryPercent: float

    class Location(BaseModel):
        lat: float
        lng: float

    class PartActivity(BaseModel):
        rateId: Optional[str]
        status: str
        bikeIdentifier: str
        location: 'ActivityModel.Location'
        bonusWithdrawnMoney: 'ActivityModel.BonusWithdrawnMoney'
        charge: 'ActivityModel.Charge'

    class Activity(TokenStatus):
        activities: List['ActivityModel.PartActivity'] = []
        errors: List[Error] = []


class ExceptionModel(TokenStatus):
    errors: Optional[List[Error]] = []
    succeeded: bool


class GeolocationModel:
    class Geolocation(BaseModel):
        countryCode: str
        placeCode: str
        cityName: str
        cityNameEng: Any
        errors: List[Error] = []
        succeeded: bool


class Settings(BaseModel):
    publicId: str
    sdkKey: str
    currency: str
    amount: float


class AcquiringSettings(BaseModel):
    acquiring: str
    settings: Settings
    errors: List
    succeeded: bool


class YookassaAddcard(BaseModel):
    confirmationUrl: str
    errors: List
    succeeded: bool


class CardForPaymentModel:
    class Result(BaseModel):
        cardSynonym: str
        publicCardId: str

    class CardForPayment(BaseModel):
        status: str
        result: 'CardForPaymentModel.Result'


class PaymentStatus(BaseModel):
    status: str
    payload: dict


class CardPayment(BaseModel):
    confirmation_url: Optional[str] = None
    error: Optional[str] = None


class RateModel:
    class Debit(BaseModel):
        culture: str
        value: float
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class Debit1(BaseModel):
        culture: str
        value: float
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class VerifyCost(BaseModel):
        culture: str
        value: int
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class Item(BaseModel):
        debit: 'RateModel.Debit1'
        isActive: bool
        isRepeat: bool
        name: Any
        periodMinute: int

    class InsuranceCost(BaseModel):
        culture: str
        value: int
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class ActivationCost(BaseModel):
        value: int = 0
        value100: int = 0
        valueFormatted: str = ""
        valueFormattedWithoutZero: str = ""

    class ForgiveCost(BaseModel):
        culture: str
        value: int
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class Rate(TokenStatus):
        activationCost: Optional['RateModel.ActivationCost'] = None
        debit: 'RateModel.Debit'
        displayName: str
        id: str
        verifyCost: 'RateModel.VerifyCost'


class TransportModel:
    class Charge(BaseModel):
        batteryForActiveInHours: float
        batteryForPassiveInHours: float
        batteryPercent: float
        remainKm: float
        status: str

    class Location(BaseModel):
        lat: float
        lng: float

    class Transport(BaseModel):
        charge: Optional['TransportModel.Charge'] = []
        displayedIdentifier: str = None
        errors: List[Error] = []
        identifier: str = None
        location: Optional['TransportModel.Location'] = []
        modelId: Optional[str] = None
        modelName: Optional[str] = None
        rate: Optional['RateModel.Rate'] = None
        state: str = None


class PlusInfoModel:
    class Entry(BaseModel):
        id: str

    class PlusInfo(TokenStatus):
        entries: List['PlusInfoModel.Entry'] = []
        errors: List[Error] = []
        succeeded: bool


class ClientInfo(BaseModel):
    appName: str
    appVersion: Any
    clientId: str


class BookingModel:
    class Location(BaseModel):
        lat: float
        lng: float

    class GeofenceZone(BaseModel):
        speedLimit: int
        type: str

    class Charge(BaseModel):
        batteryForActiveInHours: float
        batteryForPassiveInHours: float
        batteryPercent: float
        remainKm: float
        status: str

    class AbsoluteBookingsTime(BaseModel):
        differenceFromNowSeconds: int
        utcValue: str

    class BonusWithdrawnMoney(BaseModel):
        culture: str
        value: float
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class BookingActivity(BaseModel):
        absoluteBookingsTime: 'BookingModel.AbsoluteBookingsTime'

        activityId: str
        alarms: List
        allowableBookingCountPerDay: int
        allowableBookingTimeMinutes: int
        bikeIdentifier: str
        bikeModelId: str
        bonusWithdrawn: float
        bonusWithdrawnMoney: 'BookingModel.BonusWithdrawnMoney'
        bookingId: str
        bookingsLeft: int
        bookingsTime: str
        charge: 'BookingModel.Charge'
        clientInfo: ClientInfo
        closingTimeSeconds: int
        dailyPass: Any
        endZones: List[str]
        geofenceZone: 'BookingModel.GeofenceZone'
        hasDebt: bool
        lastStatusChangedDateTimeUtc: Any
        location: 'BookingModel.Location'
        lockCode: Any
        lockType: str
        order: Any
        orderingStartDateTime: Any
        orderingTimeSeconds: int
        partnerCustomerId: Any
        paymentHolidayMinutes: Any
        paymentHolidayStartDateTime: Any
        photos: Any
        rateId: Any
        referral: Any
        restrictedZones: Any
        statistics: Any
        status: str
        subscriptionInfo: Any
        transportIdentifier: str
        transportModelId: str
        useTransportLockCode: bool
        useZones: List[str]
        waitingNotConfirmed: bool
        waitingNotConfirmedFrom: Any
        waitingNotConfirmedTimeoutSeconds: Any

    class Booking(TokenStatus):
        activity: 'BookingModel.BookingActivity'
        bluetoothTokenHash: int
        errors: Optional[List[Error]] = []
        nearDepositPackage: Any
        result: str
        scooterIdentifier: Any
        scooterLocation: Any
        succeeded: bool
        type: str


class OrdersModel:
    class AbsoluteStartDateTimeUtc(BaseModel):
        utcValue: str
        differenceFromNowSeconds: int

    class AbsoluteEndDateTimeUtc(BaseModel):
        utcValue: str
        differenceFromNowSeconds: int

    class StartBikeLocation(BaseModel):
        lat: float
        lng: float

    class StartTransportLocation(BaseModel):
        lat: float
        lng: float

    class TrackItem(BaseModel):
        lat: float
        lng: float

    class Statistics(BaseModel):
        distance: float
        kcal: float
        elapsedSeconds: float
        tripCount: int

    class BonusWithdrawnMoney(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class PersonalForgiveMoney(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class CloseTransportLocation(BaseModel):
        lat: float
        long: float

    class EndTransportLocation(BaseModel):
        lat: float
        long: float

    class PersonalWithdrawnMoney(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class BonusEnrolledMoney(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class CustomerLocation(BaseModel):
        lat: float
        lng: float

    class CustomerStartLocation(BaseModel):
        lat: float
        lng: float

    class SummaryWithdrawn(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class Insurance(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class Activation(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class Rate(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class Debit(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class RateItem(BaseModel):
        debit: 'OrdersModel.Debit'
        periodMinute: int
        isRepeat: bool
        isActive: bool
        name: Any

    class RateFreeContext(BaseModel):
        isClosedWithinRateFreePeriod: bool
        rateFreeSeconds: int

    class ClientInfo(BaseModel):
        clientId: str
        deviceId: Any
        deviceModel: Any
        os: Any
        osVersion: Any
        appVersion: Any
        appName: str

    class SubscriptionInfo(BaseModel):
        subscriptionId: str
        code: str
        name: str
        provider: str

    class Amount(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class Price(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class Withdrawal1(BaseModel):
        withdrawalType: str
        amount: 'OrdersModel.Amount'
        price: 'OrdersModel.Price'
        count: int
        withdrawalTypeName: str

    class FullMoney(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class Withdrawal(BaseModel):
        withdrawals: List['OrdersModel.Withdrawal1']
        fullMoney: 'OrdersModel.FullMoney'

    class Entry(BaseModel):
        id: str
        accountId: str
        accountPhoneNumber: str
        partnerCustomerId: Any
        bikeIdentifier: str
        vendorId: str
        transportIdentifier: str
        startDateTimeUtc: str
        absoluteStartDateTimeUtc: 'OrdersModel.AbsoluteStartDateTimeUtc'
        endDateTimeUtc: str
        absoluteEndDateTimeUtc: 'OrdersModel.AbsoluteEndDateTimeUtc'
        startBikeLocation: 'OrdersModel.StartBikeLocation'
        startTransportLocation: 'OrdersModel.StartTransportLocation'
        track: List['OrdersModel.TrackItem']
        statistics: 'OrdersModel.Statistics'
        bonusWithdrawn: float
        bonusWithdrawnMoney: 'OrdersModel.BonusWithdrawnMoney'
        personalForgive: float
        personalForgiveMoney: 'OrdersModel.PersonalForgiveMoney'
        closeTransportLocation: 'OrdersModel.CloseTransportLocation'
        endTransportLocation: 'OrdersModel.EndTransportLocation'
        totalPaymentHolidaySeconds: int
        personalWithdrawn: float
        personalWithdrawnMoney: 'OrdersModel.PersonalWithdrawnMoney'
        bonusEnrolled: float
        summaryWithdrawn: 'OrdersModel.SummaryWithdrawn'
        insurance: 'OrdersModel.Insurance'
        withInsurance: bool
        activation: 'OrdersModel.Activation'
        rate: 'OrdersModel.Rate'
        rateId: str
        rateName: str
        insuranceNum: str
        cityId: str
        startUseZones: List[str]
        startTechZones: List[str]
        endTechZones: List[str]
        mobileClientId: str
        endInitiator: str
        rateItems: List['OrdersModel.RateItem']
        rating: int
        hasSubscription: bool
        isFree: bool
        rateFreeContext: 'OrdersModel.RateFreeContext'
        clientInfo: ClientInfo
        withdrawal: 'OrdersModel.Withdrawal'
        referral: Optional[str]
        errors: List

    class Orders(TokenStatus):
        totalPages: int
        totalItems: int
        currentPage: int
        itemsOnPage: int
        entries: List['OrdersModel.Entry'] = []
        errors: List[Error] = []
        succeeded: bool


class ReceiptsModel:
    class Receipts(TokenStatus):
        orderId: str
        receipts: List
        newReceiptIds: Any
        errors: List[Error] = []
        succeeded: bool


class PromoActionsModel:
    class MaxDiscountPerTrip(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class PromoActions(TokenStatus):
        isAvailable: bool
        entries: List['PromoActionsModel.Entry']
        errors: List
        succeeded: bool

    class MaxDiscountPerPromo(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class UnusedAmount(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class Entry(BaseModel):
        id: str
        promoCode: str
        discountPercentage: int
        numberOfTrips: int
        maxDiscountPerPromo: 'PromoActionsModel.MaxDiscountPerPromo'
        unusedAmount: 'PromoActionsModel.UnusedAmount'
        maxDiscountPerTrip: Optional['PromoActionsModel.MaxDiscountPerTrip']
        unusedTrips: int
        validTill: str
        inUse: bool
        activateDateTime: str
        isAboutToBurn: bool
        discountType: str


class TinkoffPayment(BaseModel):
    confirmationUrl: Optional[str] = None
    errors: List = []
    succeeded: bool


class ReferralInfoModel:
    class InviterBonus(BaseModel):
        value: float
        culture: str
        value100: int
        valueFormatted: str
        valueFormattedWithoutZero: str

    class ReferralInfo(TokenStatus):
        referralCode: str
        inviterBonus: 'ReferralInfoModel.InviterBonus'
        discountPercentForReferral: Any
        isActive: bool
        errors: List
        succeeded: bool
