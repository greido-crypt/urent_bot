import base64
import json
import random
import urllib.parse
import uuid

from db.repository import account_repository
from loader import bot_logger
from settings import PROXY_LIST, CHANNEL_ID
from .models import JWTPayload, TokenStatus, ProfileModel, CardsModel, ActivityModel, ConnectToken, \
    TransportModel, GeolocationModel, AcquiringSettings, PlusInfoModel, ExceptionModel, BookingModel, OrdersModel, \
    ReceiptsModel, PaymentProfileModel, PromoActionsModel, ReferralInfoModel, CardsDelete
from ..default import BaseRequest, BaseRequestModel
from ..vpskot import VpsKotAPI, PostData


class UrentAPI(BaseRequest):
    def __init__(self,
                 refresh_token: str,
                 access_token: str,
                 base_url: str = 'https://service.urentbike.ru/gatewayclient/api',
                 add_UrRequestData=True,
                 debug=True):

        self.__add_UrRequestData = add_UrRequestData
        self.__access_token = access_token
        self.__refresh_token = refresh_token
        self.__ur_session = str(uuid.uuid4())
        self.__ur_user_id = uuid.uuid4().hex[:24]
        self.__device_id = uuid.uuid4().hex[:16]
        self.__header_b64, self.__payload_b64, self.__signature_b64 = self.__access_token.split(".")
        self.__payload_data = JWTPayload.model_validate_json(base64.b64decode(self.__payload_b64 + "==").decode("utf-8"))
        self.__debug = debug
        self.__headers = {
            "UR-Brand": "URENT",
            "UR-Carrier-Country": "ru",
            "UR-Client-Id": "mobile.client.android",
            "UR-Country-Code": "arm",
            "UR-Device-Id": self.__device_id,
            "UR-Device-Model": "Unknown",
            "UR-Latitude": "-1.0",
            "UR-Longitude": "-1.0",
            "UR-Mobile-Store-Name": "RuStore",
            "UR-OS": "9",
            "UR-Platform": "Android",
            "UR-Request-Version": "v2",
            "UR-Session": self.__ur_session,
            # "UR-User-Id": self.__ur_user_id,
            "UR-Time-Zone": "GMT+8",
            "UR-Version": "1.55",
            "Authorization": f"Bearer {self.__access_token}",
        }
        super().__init__(base_url=base_url,
                         headers=self.__headers,
                         proxy=random.choice(PROXY_LIST),
                         timeout=5,
                         debug=debug)

    @property
    def access_token(self):
        return self.__access_token

    @property
    def refresh_token(self):
        return self.__refresh_token

    @property
    def phone_number(self):
        return self.__payload_data.phone_number

    async def _post(self, endpoint: str, **kwargs) -> BaseRequestModel:
        r"""Sends a POST request.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
        object to send in the body of the :class:`Request`.
        :param json: (optional) A JSON serializable Python object to send in the body.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        """

        # Extract important data from kwargs
        json_data = kwargs.get('json')
        data = kwargs.get('data')

        # Check if specific conditions are met
        if (json_data and self.__add_UrRequestData and json_data.get('promoCode')) or (
                data and data.get('refresh_token')):

            vps_kot_api = VpsKotAPI()
            post_data = PostData()

            # Set headers depending on the type of content (json or form data)
            if json_data:
                self._headers['Content-Type'] = "application/json"
                post_data.post_data = json_data
                del kwargs['json']
                kwargs['data'] = json.dumps(json_data, separators=(',', ':'))  # Convert JSON to string
            else:
                self._headers['Content-Type'] = "application/x-www-form-urlencoded"
                post_data.post_data = data
                del kwargs['data']
                kwargs['data'] = urllib.parse.urlencode(data, quote_via=urllib.parse.quote)  # Convert form data to URL encoding

            # Populate post_data with headers and other required fields
            post_data.post_data_type = self._headers['Content-Type']
            post_data.headers_values = [self._headers[key] for key in self._headers if key.startswith('UR-')]
            post_data.client_id = self._headers.get('UR-Client-Id')

            # Request additional data and modify headers based on response
            response_data = await vps_kot_api.request_data(post_data=post_data)
            self._headers["UR-Request-Data"] = response_data.result.UrRequestData

        # Make the actual POST request
        response = await self._make_request(method="POST", endpoint=endpoint, **kwargs)

        # Clean up headers and return the response
        try:
            del self._headers["UR-Request-Data"]
        except KeyError:
            pass  # If the key doesn't exist, just ignore

        return response

    def _token_validation(self,
                          func,
                          response: BaseRequestModel) -> bool:
        if response.status_code == 401:
            if self.__debug:
                print(f'[DEBUG] Function: {func.__name__} Wrong access token')
            return False
        return True

    async def _send_updated_access_and_refresh_token(self):
        try:
            await account_repository.updateAccessAndRefreshTokenByPhoneNumber(
                phone_number=self.__payload_data.phone_number,
                access_token=self.__access_token,
                refresh_token=self.__refresh_token)
        except Exception as e:
            return await self._send_updated_access_and_refresh_token()

    async def _send_updated_account_status_by_number(self):
        try:
            await account_repository.updateAccountStatusWrongRefreshTokenByPhoneNumber(phone_number=self.__payload_data.phone_number)
        except Exception as e:
            return await self._send_updated_account_status_by_number()

    async def _refresh_access_and_refresh_token(self) -> TokenStatus:
        """
        Получение нового __access_token'a и проверка на бан аккаунта | умирание __refresh_token'a
        """
        payload = {
            "client_id": "mobile.client.android",
            "client_secret": "95YvCeLj74Zma3SPqyH8SwgzYMtMBj5C8FxPu5xHVExwJBjMn2t7S9L4HADQaAkc",
            "grant_type": "refresh_token",
            "scope": "bike.api ordering.api location.api customers.api payment.api maintenance.api notification.api "
                     "log.api ordering.scooter.api driver.bike.lock.offo.api driver.scooter.ninebot.api identity.api "
                     "offline_access",
            "refresh_token": self.__refresh_token
        }

        try:
            del self._headers['Authorization']
        except:
            pass

        response = await self._post(endpoint='v1/connect/token', data=payload)

        if response.status_code != 200:
            await self._send_updated_account_status_by_number()
            try:
                await bot_logger.send_message(chat_id=CHANNEL_ID,
                                              text=f'<b>🚫 Окончательно умер токен:\n'
                                                   f'📞 Номер телефона: <code>{self.__payload_data.phone_number}</code></b>')
            except Exception as e:
                pass
            return TokenStatus(wrong_refresh_token=True)

        tokenModel = ConnectToken.model_validate_json(response.text)

        self.__access_token = tokenModel.access_token
        self.__refresh_token = tokenModel.refresh_token

        self._headers['Authorization'] = f'Bearer {self.__access_token}'

        await self._send_updated_access_and_refresh_token()

        return TokenStatus()

    async def mtsPayAddCard(self):
        response = await self._post(endpoint='gatewayclient/api/v1/mtspay/addcard')
        session_id = json.loads(response.text)['sessionId']
        response = await self._post(endpoint='gatewayclient/api/v1/mobile/mtsidtoken')
        ssoTokenId = json.loads(response.text)['idToken']
        session_id: str
        ssoTokenId: str
        return session_id, ssoTokenId

    async def activate_promo_code(self, promo_code: str) -> ExceptionModel | TokenStatus:
        payload = {"promoCode": promo_code}
        response = await self._post(endpoint='v2/profile/promocode', json=payload)
        if not self._token_validation(self.activate_promo_code, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.activate_promo_code(promo_code=promo_code)
        print(response.text)
        return ExceptionModel.model_validate_json(response.text)

    async def get_profile(self) -> ProfileModel | TokenStatus:
        response = await self._get(endpoint='v1/profile')
        if not self._token_validation(self.get_profile, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.get_profile()
        return ProfileModel.Profile.model_validate_json(response.text)

    async def get_cards(self) -> TokenStatus | CardsModel.Cards:
        response = await self._get(endpoint='v1/cards')
        if not self._token_validation(self.get_cards, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.get_cards()
        return CardsModel.Cards.model_validate_json(response.text)

    async def get_payment_profile(self):
        response = await self._get(endpoint='v1/payment/profile')
        if not self._token_validation(self.get_payment_profile, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.get_payment_profile()
        return PaymentProfileModel.PaymentProfile.model_validate_json(response.text)

    async def get_activity(self):
        response = await self._get(endpoint='v1/activity')
        if not self._token_validation(self.get_activity, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.get_activity()
        return ActivityModel.Activity.model_validate_json(response.text)

    async def get_orders(self):
        params = {"cPage": 1, "iOnPage": 99, "order": "StartDateTimeUtc:desc"}
        response = await self._get(endpoint="v1/orders/my", params=params)
        if not self._token_validation(self.get_orders, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.get_orders()
        return OrdersModel.Orders.model_validate_json(response.text)

    async def get_scooter_info(self, transport: str):
        """
        :param transport: Like this 'S.128308'
        """
        params = {'isQrCode': 'false', 'referral': ''}
        response = await self._get(endpoint=f"v1/transports/{transport}", params=params)
        if not self._token_validation(self.get_scooter_info, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.get_scooter_info(transport=transport)
        return TransportModel.Transport.model_validate_json(response.text)

    async def get_request_location(self, activity_info: ActivityModel.Activity):
        """
        param: scooter_id : S.123123`
        """
        response = await self._post(
            endpoint=f"v3/transports/{activity_info.activities[0].bikeIdentifier}/requestlocation")
        if not self._token_validation(self.get_request_location, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.get_request_location(activity_info)
        return ExceptionModel.model_validate_json(response.text)

    async def get_geolocation(self, lat: float, lng: float):
        params = {'lat': lat, 'lng': lng}
        response = await self._get(endpoint=f"v1/location/geolocation", params=params)
        if not self._token_validation(self.get_geolocation, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.get_geolocation(lat=lat, lng=lng)
        return GeolocationModel.Geolocation.model_validate_json(response.text)

    async def get_payment_acquiring_settings(self):
        params = {'countryCode': "arm",
                  'cityName': "Китай",
                  "priorityAcquiring": "Yookassa"}
        response = await self._get(endpoint="v1/payment/acquiring_settings", params=params)
        if not self._token_validation(self.get_payment_acquiring_settings, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.get_payment_acquiring_settings()
        return AcquiringSettings.model_validate_json(response.text)

    async def remove_card(self, card_id: str):
        response = await self._delete(endpoint=f"v1/cards/cards/{card_id}")
        if not self._token_validation(self.remove_card, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.remove_card(card_id)
        return CardsDelete.Model.model_validate_json(response.text)

    async def start_drive(self,
                          scooter_info: TransportModel.Transport,
                          rateId: str,
                          promo_code: str = ""):
        json_data = {"tryingToWithdrawMtsCashback": False, "locationLat": scooter_info.location.lat,
                     "locationLng": scooter_info.location.lng, "promoCode": promo_code, "isQrCode": False,
                     "rateId": rateId, "referral": "", "Identifier": scooter_info.identifier,
                     "withInsurance": False}
        response = await self._post(endpoint="v1/order/make", json=json_data)
        if not self._token_validation(self.start_drive, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.start_drive(scooter_info, rateId)
        return ExceptionModel.model_validate_json(response.text)

    async def stop_drive(self, activity_info: ActivityModel.Activity):

        locations = random.choice([{"lat": 44.99708938598633, "lng": 39.07448959350586},
                                   {"lat": 45.01229183333333, "lng": 39.07393233333333},
                                   {"lat": 44.55036283333334, "lng": 38.0856945},
                                   {"lat": 44.5753125, "lng": 38.066902166666665},
                                   {"lat": 44.87790683333333, "lng": 37.33355566666667},
                                   {"lat": 44.90170366666666, "lng": 37.3204025},
                                   {"lat": 43.41010516666667, "lng": 39.936585666666666},
                                   {"lat": 43.387023500000005, "lng": 39.99113166666667},
                                   {"lat": 43.920260999999996, "lng": 39.31842066666666},
                                   ])
        json_data = {
            "locationLat": locations["lat"],
            "locationLng": locations["lng"],
            "Identifier": activity_info.activities[0].bikeIdentifier
        }
        response = await self._post(endpoint="v1/order/end", json=json_data)
        if not self._token_validation(self.stop_drive, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.stop_drive(activity_info)
        return ExceptionModel.model_validate_json(response.text)

    async def remove_pause_drive(self, activity_info: ActivityModel.Activity) -> TokenStatus | ExceptionModel:
        json_data = {
            "locationLat": activity_info.activities[0].location.lat,
            "locationLng": activity_info.activities[0].location.lng,
            "isQrCode": False,
            "rateId": "",
            "Identifier": activity_info.activities[0].bikeIdentifier,
            "withInsurance": False
        }
        response = await self._post(endpoint="v1/order/resume", json=json_data)
        if not self._token_validation(self.pause_drive, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.pause_drive(activity_info)
        return ExceptionModel.model_validate_json(response.text)

    async def pause_drive(self, activity_info: ActivityModel.Activity) -> ExceptionModel | TokenStatus:
        json_data = {
            "locationLat": activity_info.activities[0].location.lat,
            "locationLng": activity_info.activities[0].location.lng,
            "isQrCode": False,
            "rateId": "",
            "Identifier": activity_info.activities[0].bikeIdentifier,
            "withInsurance": False
        }
        response = await self._post(endpoint="v1/order/wait", json=json_data)
        if not self._token_validation(self.pause_drive, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.pause_drive(activity_info)
        return ExceptionModel.model_validate_json(response.text)

    async def booking_cancel(self, activity_info: ActivityModel.Activity) -> ExceptionModel | TokenStatus:
        json_data = {
            "locationLat": activity_info.activities[0].location.lat,
            "locationLng": activity_info.activities[0].location.lng,
            "Identifier": activity_info.activities[0].bikeIdentifier
        }
        response = await self._post(endpoint="v1/booking/cancel", json=json_data)
        if not self._token_validation(self.booking_cancel, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.booking_cancel(activity_info)
        return ExceptionModel.model_validate_json(response.text)

    async def booking_make(self, scooter_info: TransportModel.Transport) -> TokenStatus | BookingModel:
        json_data = {
            "locationLat": scooter_info.location.lat,
            "locationLng": scooter_info.location.lng,
            "Identifier": scooter_info.identifier
        }
        response = await self._post(endpoint="v1/booking/make", json=json_data)
        if not self._token_validation(self.booking_make, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.booking_make(scooter_info)
        return BookingModel.Booking.model_validate_json(response.text)

    async def get_plus_info(self):
        response = await self._get(endpoint="v1/subscriptions/my")
        if not self._token_validation(self.get_plus_info, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.get_plus_info()
        return PlusInfoModel.PlusInfo.model_validate_json(response.text)

    async def get_ride_payment_info(self, ride_id: str):
        response = await self._get(endpoint=f"v1/paymentinfo/{ride_id}/receipts")
        if not self._token_validation(self.get_ride_payment_info, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.get_ride_payment_info(ride_id)
        return ReceiptsModel.Receipts.model_validate_json(response.text)

    async def get_referral_info(self):
        params = {'placeCode': 'AM'}
        response = await self._get(endpoint="v1/profile/my/referralinfo", params=params)
        if not self._token_validation(self.get_ride_payment_info, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.get_referral_info()
        return ReferralInfoModel.ReferralInfo.model_validate_json(response.text)

    async def get_promo_actions(self):
        params = {'placeCode': 'RU'}
        response = await self._get(endpoint="v1/profile/my/promoactions", params=params)
        if not self._token_validation(self.get_ride_payment_info, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self.get_promo_actions()
        return PromoActionsModel.PromoActions.model_validate_json(response.text)
