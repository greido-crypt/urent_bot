import asyncio
import json
import random
import string
import time
from urllib import parse

from bs4 import BeautifulSoup

from .models import YookassaAddcard, TokenStatus, CardPayment, TinkoffPayment
from .urent import UrentAPI
from ..yoomoney import YooMoneyAPI
from ..zeon import ZeonAPI


class PaymentUrent(UrentAPI):
    async def _yookassaAddCardWebview(self, params: dict = None) -> YookassaAddcard | TokenStatus:
        if params is None:
            params = {"cardPayType": "bank_card"}
        response = await self._post(endpoint='v1/yookassa/addcard/webview', params=params)
        if not self._token_validation(self._yookassaAddCardWebview, response):
            response_token = await self._refresh_access_and_refresh_token()
            if response_token.wrong_refresh_token:
                return response_token
            return await self._yookassaAddCardWebview()
        return YookassaAddcard.model_validate_json(response.text)

    async def link_card_mir(self) -> str:
        response = await self._yookassaAddCardWebview()
        confirmation_url = response.confirmationUrl
        parsed_url = parse.urlparse(confirmation_url)
        query_params = parse.parse_qs(parsed_url.query)
        order_id = query_params.get('orderId')[0]
        return await YooMoneyAPI().getMirPayPaymentLink(order_id=order_id)

    async def link_card_tinkoff(self):
        json_data = {"cardPayType": "tinkoff", "os": "Android", "url": "https://t.me/shadow_urent_bot"}
        response = await self._post(endpoint='v1/cloudpayments/addcard/aps', json=json_data)
        return TinkoffPayment.model_validate_json(response.text)

    async def link_card_sberbank(self) -> YookassaAddcard | TokenStatus:
        params = {"cardPayType": "sberbank", "url": "https://t.me/shadow_urent_bot"}
        return await self._yookassaAddCardWebview(params=params)

    async def yookassa_payment(self,
                               pan: str,
                               expireDate: str,
                               csc: str) -> CardPayment:
        """
        pan: card_number
        expireDate: 202409: 20 + year + month
        csc: cvc
        """
        payment_model = CardPayment()
        response = await self._yookassaAddCardWebview()
        confirmation_url = response.confirmationUrl
        print(confirmation_url)
        parsed_url = parse.urlparse(confirmation_url)
        query_params = parse.parse_qs(parsed_url.query)
        order_id = query_params.get('orderId')[0] if 'orderId' in query_params else None
        yoomoney_api = YooMoneyAPI()

        response = await yoomoney_api.yoomoneyStoreCardForPayment(pan=pan,
                                                                  expireDate=expireDate,
                                                                  csc=csc,
                                                                  requestId=order_id)
        sk = ''.join(random.choice(string.hexdigits + string.digits) for _ in range(40))
        sk = f'{sk}:{time.time()}'
        await yoomoney_api.anyCardStart(orderId=order_id, cardSynonym=response.result.cardSynonym, sk=sk)
        await asyncio.sleep(6)
        response = await yoomoney_api.paymentStatus(orderId=order_id, sk=sk)

        if response.payload['status'] == "Failure":
            payment_model.error = 'Лимит по карте, попробуйте выбрать другую карту'
            return payment_model

        zeon_api = ZeonAPI(port=228, debug=True)

        url = response.payload['authParams'].get('url')
        methodData = response.payload['authParams']['payload'].get('methodData')
        methodUrl = response.payload['authParams']['payload'].get('methodUrl')
        orderN = response.payload['authParams']['payload'].get('orderN')
        print('[url]', url)
        print('[methodData]', methodData)
        print('[methodUrl]', methodUrl)
        print('[orderN]', orderN)
        acsUri = response.payload['authParams']['payload'].get('acsUri')
        MD = response.payload['authParams']['payload'].get('MD')
        PaReq = response.payload['authParams']['payload'].get('PaReq')
        TermUrl = response.payload['authParams']['payload'].get('TermUrl')
        print('[acsUri]',acsUri)
        print('[MD]',MD)
        print('[PaReq]',PaReq)
        print('[TermUrl]',TermUrl)

        creq = response.payload['authParams']['payload'].get('creq')
        print('[CREQ]',creq)
        if methodData:
            """
            """
            response = await zeon_api.urent_payment_create_mir(payment_url=url,
                                                               methodUrl=methodUrl,
                                                               orderN=orderN,
                                                               methodData=methodData)
            json_response: dict = json.loads(response.text)
            payment_model.confirmation_url = json_response.get('url')
            return payment_model

        elif PaReq:
            """
            """
            response = await zeon_api.urent_payment_create_visa(payment_url=acsUri,
                                                                pa_req=PaReq,
                                                                md=MD,
                                                                term_url=TermUrl)
            json_response: dict = json.loads(response.text)
            payment_model.confirmation_url = json_response.get('url')
            return payment_model

        elif creq:
            """
            """
            response = await zeon_api.urent_payment_create_ecom_creq_mir(payment_url=acsUri,
                                                                         creq=creq)
            json_response: dict = json.loads(response.text)
            payment_model.confirmation_url = json_response.get('url')
            return payment_model

        payment_model.error = '<b>Не удалось провести привязку карты, обратитесь в техническую поддержку для решения проблемы</b>'
        return payment_model

    async def _payment_ecommpay(self,
                                ecom_pay_body: str):
        json_ecom_pay_body = json.loads(ecom_pay_body)
        self._base_url = 'https://paymentpage.ecpru.com'
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 11; TECNO BD4a Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.66 Mobile Safari/537.36"
        }
        return await self._post(endpoint='payment', json=json_ecom_pay_body)

    async def _process_payment(self,
                               wsid_value: str,
                               csrf_token: str,
                               pan: int | str,
                               expireDate: int | str,
                               csc: int | str):
        self._base_url = 'https://paymentpage.ecpru.com'
        data = {
            "wsid": f"{wsid_value}",
            "PaymentData[pan]": f"{pan}",
            "PaymentData[month]": f"{expireDate.split('/')[0]}",
            "PaymentData[year]": f"20{expireDate.split('/')[1]}",
            "PaymentData[month_year]": f"{expireDate.split('/')[0]} / {expireDate.split('/')[1]}",
            "PaymentData[cvv]": f"{csc}",
            "operation": "verify",
            "payment_method_code": "card",
            "payment_method_type": "1",
            "screenWidth": "360",
            "screenHeight": "800"
        }

        self._headers = {"x-csrf-token": f'{csrf_token}',
                         "User-Agent": "Mozilla/5.0 (Linux; Android 11; TECNO BD4a Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.66 Mobile Safari/537.36"
                         }

        return await self._post(endpoint='process/payment', data=data)

    async def _process_status(self,
                              wsid_value: str,
                              csrf_token: str,
                              request_id: int | str):
        # self.base_url = 'https://paymentpage.ecommpay.com'
        self.base_url = 'https://paymentpage.ecpru.com'
        data = {
            "request_id": f"{request_id}",
            "project_id": "69652",
            "options": '{"ctrl_expiry_format":"2","ctrl_show_holder_name":"0","ctrl_custom_card_holder":"2","ctrl_show_placeholders":"1","ctrl_number_format":"1","ctrl_expiry_year_amount":"15","ctrl_show_footer":"1","ctrl_show_header":"1","ctrl_type_display_mode":"0","ctrl_show_saved_accounts":"1","ctrl_list_show_name":"0","ctrl_aps_cascading":"0","ctrl_show_clarification_fields_description":"0","ctrl_ecp_logo_v4":"0","ctrl_hide_monetix_logo_v3":"0","ctrl_display_in_painter":"0","ctrl_skip_method_selection_page":"0","ctrl_enable_microframe_mode":"0"}',
            "payment_method_code": "card",
            "payment_method_type": "1",
            "payment_method_alias": "null",
            "payment_method_subtype_id": "null",
            "wsid": f"{wsid_value}",
            "screenWidth": "360",
            "screenHeight": "800"
        }

        self._headers = {
            "x-csrf-token": f'{csrf_token}',
                         }

        return await self._post(endpoint='process/status', data=data)

    async def _ecom_pay_webview(self):
        json_data = {"amount": 15.0, "currency": "ru-RU", "projectId": "69652"}
        return await self._post(endpoint='v1/ecommpay/webview', json=json_data)

    async def ecom_pay_payment(self,
                               pan: int | str,
                               expireDate: str,
                               csc: int | str) -> CardPayment:
        """
        pan: card_number
        expireDate: 24/09: year + / + month
        csc: cvc
        """

        payment_model = CardPayment()

        response = await self._ecom_pay_webview()
        json_web_view_data = json.loads(response.text)
        ecom_pay_body: str = json_web_view_data['body']
        """
        {
        "card_number": card_info.card_number,
        "month": f"{int(card_info.exp[:2])}",
        "year": f"{int(card_info.exp[~1:])}",
        "cvv": card_info.cvv
        }
        """
        payment_info = await self._payment_ecommpay(ecom_pay_body=ecom_pay_body)

        soup = BeautifulSoup(payment_info.text, 'html.parser')

        wsid_input = soup.find('input', {'name': 'wsid'})
        wsid_value = wsid_input.get('value')
        print('[PAYMENT DEBUG] wsid_value:', wsid_value)
        csrf_meta = soup.find('meta', {'name': 'csrf-token'})
        csrf_token = csrf_meta.get('content')
        print('[PAYMENT DEBUG] csrf_token:', csrf_token)
        await asyncio.sleep(2)
        process_payment_info = await self._process_payment(wsid_value=wsid_value,
                                                           csrf_token=csrf_token,
                                                           pan=pan,
                                                           expireDate=expireDate,
                                                           csc=csc)
        payment_coms = json.loads(process_payment_info.text)
        request_id = payment_coms['metadata']['request_id']
        # await asyncio.sleep(10)
        process_status_info = await self._process_status(wsid_value=wsid_value,
                                                         csrf_token=csrf_token,
                                                         request_id=request_id)
        get_ds_method_data = json.loads(process_status_info.text)

        zeon_api = ZeonAPI(port=228, debug=True)

        if get_ds_method_data.get('redirect') and 'PaReq' in get_ds_method_data['redirect']['params']:
            pa_req = get_ds_method_data['redirect']['params']['PaReq']
            md = get_ds_method_data['redirect']['params']['MD']
            url = get_ds_method_data['redirect']['url']
            term_url = get_ds_method_data['redirect']['params']['TermUrl']

            response = await zeon_api.urent_payment_create_visa(payment_url=url,
                                                                pa_req=pa_req,
                                                                md=md,
                                                                term_url=term_url)

            json_response: dict = json.loads(response.text)
            payment_model.confirmation_url = json_response.get('url')
            return payment_model

        DSMethodData = get_ds_method_data['metadata']['threeds2']['iframe']['params']['3DSMethodData']
        threeDSMethodData = get_ds_method_data['metadata']['threeds2']['iframe']['params']['threeDSMethodData']
        termUrl = get_ds_method_data['metadata']['threeds2']['iframe']['url']
        print(termUrl)
        print(threeDSMethodData)
        data = {
            "3DSMethodData": f"{DSMethodData}",
            "threeDSMethodData": f"{threeDSMethodData}"
        }
        self._base_url = termUrl
        get_notification = await self._post(data=data, endpoint='')
        soup = BeautifulSoup(get_notification.text, 'html.parser')
        notification_url = soup.find('form', {'id': 'callbackForm'}).get('action')
        three_ds_data = soup.find('input', {'id': 'threeDSMethodData'}).get('value')

        data = {"threeDSMethodData": three_ds_data}
        self._base_url = notification_url
        response = await self._post(data=data, endpoint='', verify_ssl=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        notification_url_input = soup.find("input", id="threeDSMethodNotificationURL")
        if notification_url_input:
            # Extract the threeDSServerTransID and form action URL
            threeDSMethodNotificationURL = soup.find("input", id="threeDSMethodNotificationURL")["value"]
            threeDSMethodData = soup.find("input", id="threeDSMethodData")["value"]
            self._base_url = threeDSMethodNotificationURL
            data = {"threeDSMethodData": threeDSMethodData}
            await self._post(data=data, endpoint='')
            await asyncio.sleep(10)

        process_status_info = await self._process_status(wsid_value, csrf_token, request_id)
        json_processed_data = json.loads(process_status_info.text)

        payment_url = json_processed_data['redirect']['url']
        creq = json_processed_data['redirect']['params']['creq']

        response = await zeon_api.urent_payment_create_ecom_creq_mir(payment_url=payment_url, creq=creq)
        json_response: dict = json.loads(response.text)
        payment_model.confirmation_url = json_response.get('url')
        return payment_model
