import asyncio
import datetime
import json
import time
import traceback
from io import BytesIO
from urllib import parse

import aiofiles
from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from api import UrentAPI, PaymentUrent
from api.mts import MtsAPI, MtsPay
from api.zeon import ZeonAPI
from data import generate_delete_account_kb, generate_back_to_account_kb, generate_account_kb, generate_payment_kb
from data.keyboards import generate_html_page, generate_history_url, generate_go_to_support_kb, \
    generate_payment_service_kb
from db.models import Accounts
from db.repository import account_repository, cards_repository
from db.repository import rides_repository
from loader import UserStates, bot_logger
from settings import CHANNEL_ID, ADMIN_LIST, HELP_URL
from utils import PaymentCardsPaginator
from ..main_menu import personal_area

account_router = Router(name='account_router')


@account_router.callback_query(F.data.startswith((
        "history_rides",
        "find_scooter",
        'booking_make',
        'booking_cancel',
        "start_tariff",
        'check_payment',
        "select_card",
        'pay_card_mir',
        'pay_card',
        "get_cost",
        "start_drive",
        "stop_drive",
        'pause_drive',
        'remove_pause_drive',
        'add_credit_card',
        'remove_cards',
        'get_drive_cost',
        'remove_acc',
        'accept_remove_acc',
        'activate_promo_code',
        'activate_free_start')), any_state)
async def read_handlers_in_account(call: CallbackQuery, state: FSMContext, bot: Bot):
    list_call_data = call.data.split(':')
    method = list_call_data[0]
    account_id = int(list_call_data[1])
    account_data = await account_repository.getAccountByAccountId(account_id=account_id)

    if not account_data:
        await call.message.answer("<b>❌ Ошибка при нахождении аккаунта</b>")
        return await personal_area(call)

    if account_data.is_deleted and call.from_user.id not in ADMIN_LIST:
        return await personal_area(call)

    urent_api = UrentAPI(refresh_token=account_data.refresh_token,
                         access_token=account_data.access_token,
                         add_UrRequestData=False,
                         debug=True)

    payment_api = PaymentUrent(refresh_token=urent_api.refresh_token,
                               access_token=urent_api.access_token,
                               add_UrRequestData=False,
                               debug=True)

    payment_profile = await urent_api.get_payment_profile()

    if payment_profile.wrong_refresh_token:
        await call.message.edit_text(text=f"❌ <b>Ошибка: Токен обновления устарел.\n"
                                          f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                          f"🎫 Купон: <code>{account_data.coupon}</code>",
                                     reply_markup=generate_go_to_support_kb())

        await bot_logger.send_message(chat_id=CHANNEL_ID,
                                      text=f"❌ <b>Ошибка: Токен обновления устарел.\n"
                                           f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                           f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                           f"💜 Пользователь: @{call.from_user.username}</b>")
        return await personal_area(call)

    activity_info, cards_info = await asyncio.gather(urent_api.get_activity(),
                                                     urent_api.get_cards())

    print('[METHOD]', method)

    if method == 'accept_remove_acc':
        if activity_info.activities:
            await call.answer('❌ Сначала закончите поездку', show_alert=True)
            return await get_account_data(call, state)

        elif cards_info.entries:
            await call.answer('❌ Сначала отвяжите карты', show_alert=True)
            return await get_account_data(call, state)

        await bot_logger.send_message(chat_id=CHANNEL_ID,
                                      text=f'<b>🚀 Аккаунт был удален:\n'
                                           f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                           f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                           f"💜 Пользователь: @{call.from_user.username}</b>")

        await account_repository.updateAccountIsDeletedStatusByAccountId(account_id=account_data.id)

        return await personal_area(call)

    elif method == 'activate_free_start':
        mts_api = MtsAPI(ya_token=account_data.ya_token)
        response = await mts_api.activate_mts_premium(phone_number=account_data.phone_number,
                                                      content_id='c3be0b5c-760e-43e5-b089-24336ced1950')
        if not response.subscriptionId:
            response = await mts_api.activate_mts_premium(phone_number=account_data.phone_number,
                                                          content_id='9a1ca77a-bec5-4df5-a0a2-dedc974143e1')
        return await get_account_data(call, state)

    elif method == 'remove_acc':
        if activity_info.activities:
            await call.answer('❌ Сначала закончите поездку', show_alert=True)
            return await get_account_data(call, state)

        elif cards_info.entries:
            await call.answer('❌ Сначала отвяжите карты', show_alert=True)
            return await get_account_data(call, state)

        return await call.message.edit_text(text='<b>Вы точно хотите удалить аккаунт?</b>',
                                            reply_markup=generate_delete_account_kb(account_data.id))

    elif method == "remove_cards":
        if not cards_info.entries:
            await call.answer('У вас не привязаны карты', show_alert=True)
            return await get_account_data(call, state)

        elif not activity_info.activities:
            cards_id = [data_card.id for data_card in cards_info.entries]
            for card_id in cards_id:
                response = await urent_api.remove_card(card_id=card_id)
                if response.errors:
                    return await call.answer(show_alert=True, text=response.errors[0].value[0])

            await bot_logger.send_message(chat_id=CHANNEL_ID,
                                          text=f'<b>✅ Все привязанные карты были удалены из аккаунта:\n'
                                               f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                               f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                               f"💜 Пользователь: @{call.from_user.username}</b>")

            await call.answer(text='✅ Все привязанные карты были удалены из аккаунта', show_alert=True)
            return await get_account_data(call, state)

    elif method == 'find_scooter':

        if not activity_info.activities:
            return await get_account_data(call, state)

        response = await urent_api.get_request_location(activity_info=activity_info)

        if response.errors:
            error = response.errors[0].value[0]
            await bot_logger.send_message(chat_id=CHANNEL_ID, text=f'<b>🚫 Ошибка при звонке: {error}\n'
                                                                   f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                                                   f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                                                   f"💜 Пользователь: @{call.from_user.username}</b>")
            return await call.message.edit_text(f'Ошибка при звонке: {error}',
                                                reply_markup=generate_back_to_account_kb(account_id=account_data.id))

    elif method == 'booking_make':
        if not cards_info.entries:
            await call.answer('У вас не привязана карта', show_alert=True)
            return await get_account_data(call, state)

        elif activity_info.activities:
            await call.answer('У вас уже имеется активность', show_alert=True)
            return await get_account_data(call, state)

        scooter_id = list_call_data[2]
        scooter_info = await urent_api.get_scooter_info(transport=scooter_id)
        response = await urent_api.booking_make(scooter_info=scooter_info)

        if response.errors:
            error = response.errors[0].value[0]
            await bot_logger.send_message(chat_id=CHANNEL_ID,
                                          text=f'🚫 Ошибка при бронировании самоката: {error}\n'
                                               f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                               f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                               f"💜 Пользователь: @{call.from_user.username}</b>")

            return await call.message.edit_text(f'Ошибка при бронировании самоката: {error}',
                                                reply_markup=generate_back_to_account_kb(account_id=account_data.id))
        return await get_account_data(call, state)

    elif method == 'booking_cancel':
        if not activity_info.activities:
            return await get_account_data(call, state)
        response = await urent_api.booking_cancel(activity_info=activity_info)

        if response.errors:
            error = response.errors[0].value[0]
            await bot_logger.send_message(chat_id=CHANNEL_ID, text=f'<b>🚫 Ошибка при снятии брони: {error}\n'
                                                                   f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                                                   f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                                                   f"💜 Пользователь: @{call.from_user.username}</b>")
            return await call.message.edit_text(f'Ошибка при снятии брони: {error}',
                                                reply_markup=generate_back_to_account_kb(account_id=account_data.id))
        return await get_account_data(call, state)

    elif method == "start_tariff":

        if not cards_info.entries:
            await call.answer('У вас не привязана карта', show_alert=True)
            return await get_account_data(call, state)

        elif activity_info.activities:
            return await get_account_data(call, state)

        id_tariff: str = list_call_data[2]
        scooter_id: str = list_call_data[3]

        scooter_info = await urent_api.get_scooter_info(transport=f'{scooter_id}')

        geolocation_info, promo_actions, plus_info = await asyncio.gather(urent_api.get_geolocation(lat=scooter_info.location.lat,
                                                                                                    lng=scooter_info.location.lng),
                                                                          urent_api.get_promo_actions(),
                                                                          urent_api.get_plus_info())
        # 0 - поездка по промокодам
        # 1 - поездка по баллам
        # 2 - поездка по баллам + промокод

        account_points = payment_profile.bonuses.value

        if plus_info.entries:
            activation_cost = 0
        elif scooter_info.rate.activationCost:
            activation_cost = scooter_info.rate.activationCost.value
        else:
            activation_cost = 0

        debit_value = scooter_info.rate.debit.value

        if account_data.account_functionality == 0:
            if not promo_actions.entries:
                return call.message.edit_text('<b>❌ Закончились поездки со скидкой</b>',
                                              reply_markup=generate_back_to_account_kb(account_id=account_data.id))

            discount_percentage = promo_actions.entries[0].discountPercentage
            unused_amount = promo_actions.entries[0].unusedAmount.value

            if not promo_actions.entries[0].maxDiscountPerTrip:
                max_amount_with_discount = (unused_amount * (1 + (discount_percentage / 100)) - activation_cost)

            else:
                max_discount_per_trip = promo_actions.entries[0].maxDiscountPerTrip.value
                unused_amount = min(max_discount_per_trip, unused_amount)
                max_amount_with_discount = (unused_amount * (1 + (discount_percentage / 100)) - activation_cost)

            if promo_actions.entries[0].unusedTrips > 1:
                time_in_minutes = min(max_amount_with_discount / debit_value, 100 / debit_value)

            else:
                time_in_minutes = max_amount_with_discount / debit_value

            promo_code = promo_actions.entries[0].promoCode
            response = await urent_api.start_drive(scooter_info=scooter_info, rateId=id_tariff, promo_code=promo_code)

        elif account_data.account_functionality == 1:
            time_in_minutes = (account_points - activation_cost) / debit_value
            response = await urent_api.start_drive(scooter_info=scooter_info, rateId=id_tariff)

        elif account_data.account_functionality == 2:
            if not promo_actions.entries:
                time_in_minutes = (account_points - activation_cost) / debit_value
                response = await urent_api.start_drive(scooter_info=scooter_info, rateId=id_tariff)
            else:
                discount_percentage = promo_actions.entries[0].discountPercentage
                unused_amount = promo_actions.entries[0].unusedAmount.value

                if not promo_actions.entries[0].maxDiscountPerTrip:
                    max_amount_with_discount = (unused_amount * (1 + (discount_percentage / 100)) - activation_cost)

                else:
                    max_discount_per_trip = promo_actions.entries[0].maxDiscountPerTrip.value
                    unused_amount = min(max_discount_per_trip, unused_amount)
                    max_amount_with_discount = (unused_amount * (1 + (discount_percentage / 100)) - activation_cost)

                discount_time_in_minutes = (unused_amount * (
                        1 + (discount_percentage / 100)) - activation_cost) / debit_value
                points_time_in_minutes = (account_points * (
                        1 + (discount_percentage / 100)) - activation_cost) / debit_value

                time_in_minutes = min(discount_time_in_minutes, points_time_in_minutes)

                promo_code = promo_actions.entries[0].promoCode
                response = await urent_api.start_drive(scooter_info=scooter_info, rateId=id_tariff,
                                                       promo_code=promo_code)

        else:
            time_in_minutes = 0
            response = await urent_api.start_drive(scooter_info=scooter_info, rateId=id_tariff)

        finished_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=time_in_minutes)

        await asyncio.sleep(4)

        activity_info = await urent_api.get_activity()

        if not activity_info.activities:
            try:
                error = response.errors[0].value[0]
                await bot_logger.send_message(chat_id=CHANNEL_ID, text=f'<b>🚫 Ошибка при запуске самоката: {error}\n'
                                                                       f'🛴 Номер самоката: <code>{scooter_id}</code>\n'
                                                                       f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                                                       f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                                                       f"💜 Пользователь: @{call.from_user.username}</b>")

            except Exception as error:
                await bot_logger.send_message(chat_id=CHANNEL_ID, text=f'<b>🚫 Ошибка при запуске самоката: {error}\n'
                                                                       f'🛴 Номер самоката: <code>{scooter_id}</code>\n'
                                                                       f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                                                       f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                                                       f"💜 Пользователь: @{call.from_user.username}</b>")

            return await call.message.edit_text(f'<b>🚫 Ошибка при запуске самоката: {error}</b>',
                                                reply_markup=generate_back_to_account_kb(account_id=account_data.id))

        await bot_logger.send_message(chat_id=CHANNEL_ID, text=f'<b>✅ Успешно запущен самокат:\n'
                                                               f'🛴 Номер самоката: <code>{scooter_id}</code>\n'
                                                               f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                                               f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                                               f"🌃 Город: <code>{geolocation_info.cityName}</code>\n"
                                                               f"💜 Пользователь: @{call.from_user.username}</b>")

        if not call.message.reply_markup.inline_keyboard[0][0].callback_data == 'off_auto_stop':
            return await get_account_data(call, state)

        try:
            await rides_repository.add_ride(account_id=account_data.id,
                                            rate_id=id_tariff,
                                            bot_id=bot.id,
                                            city=geolocation_info.cityName,
                                            finished_time=finished_time)
        except Exception as error:
            return await bot_logger.send_message(chat_id=CHANNEL_ID,
                                                 text=f'<b>🚫 Ошибка при добавлении авто-завершения: {error}\n'
                                                      f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                                      f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                                      f"💜 Пользователь: @{call.from_user.username}</b>")
        finally:
            return await get_account_data(call, state)

    elif method == "start_drive":
        if not cards_info.entries:
            await call.answer('У вас не привязана карта', show_alert=True)
            return await get_account_data(call, state)

        elif not activity_info.activities or activity_info.activities[0].status == 'Booking':
            await state.update_data(cancel_message=call, account_data=account_data)

            await call.message.edit_text(
                text='<b>✏️ Пришлите номер самоката в виде текста.\n'
                     '<i>Пример: 192-156 или же 192156</i></b>',
                reply_markup=generate_back_to_account_kb(account_id=account_data.id))

            return await state.set_state(UserStates.input_scooter)

        return await get_account_data(call, state)

    elif method == 'stop_drive':
        if not activity_info.activities:
            return await get_account_data(call, state)

        response = await urent_api.stop_drive(activity_info=activity_info)
        if response.errors:
            error = response.errors[0].value[0]
            await bot_logger.send_message(chat_id=CHANNEL_ID, text=f'<b>🚫 Ошибка при завершении самоката: {error}\n'
                                                                   f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                                                   f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                                                   f"💜 Пользователь: @{call.from_user.username}</b>")
            return await call.answer(f'❌ Ошибка при завершении самоката: {error}', show_alert=True)

        await rides_repository.update_upd_date_by_account_id(account_id=account_data.id)
        await bot_logger.send_message(chat_id=CHANNEL_ID, text=f'<b>✅ Поездка успешно завершена:\n'
                                                               f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                                               f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                                               f"💜 Пользователь: @{call.from_user.username}</b>")
        await call.answer('✅ Поездка успешно завершена', show_alert=True)
        return await get_account_data(call, state)

    elif method == "remove_pause_drive":
        if not activity_info.activities:
            return await get_account_data(call, state)

        response = await urent_api.remove_pause_drive(activity_info=activity_info)

        if response.errors:
            error = response.errors[0].value[0]
            await bot_logger.send_message(chat_id=CHANNEL_ID, text=f'<b>🚫 Ошибка при снятии самоката с паузы: {error}\n'
                                                                   f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                                                   f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                                                   f"💜 Пользователь: @{call.from_user.username}</b>")
            await call.answer(f'Ошибка при снятии самоката с паузы: {error}', show_alert=True)

        await bot_logger.send_message(chat_id=CHANNEL_ID, text=f'<b>✅ Самокат снят с паузы:\n'
                                                               f'🛴 Номер самоката: <code>{activity_info.activities[0].bikeIdentifier}</code>\n'
                                                               f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                                               f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                                               f"💜 Пользователь: @{call.from_user.username}</b>")

        await call.answer(f'Самокат снят с паузы', show_alert=True)
        return await get_account_data(call, state)

    elif method == "pause_drive":
        if not activity_info.activities:
            return await get_account_data(call, state)

        response = await urent_api.pause_drive(activity_info=activity_info)

        if response.errors:
            error = response.errors[0].value[0]
            await bot_logger.send_message(chat_id=CHANNEL_ID,
                                          text=f'<b>🚫 Ошибка при постановке самоката на паузу: {error}\n'
                                               f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                               f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                               f"💜 Пользователь: @{call.from_user.username}</b>")
            return await call.answer(f'Ошибка при постановке самоката на паузу: {error}', show_alert=True)

        await bot_logger.send_message(chat_id=CHANNEL_ID, text=f'<b>✅ Самокат поставлен на паузу:\n'
                                                               f'🛴 Номер самоката: <code>{activity_info.activities[0].bikeIdentifier}</code>\n'
                                                               f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                                               f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                                               f"💜 Пользователь: @{call.from_user.username}</b>")

        await call.answer('✅ Самокат поставлен на паузу', show_alert=True)
        return await get_account_data(call, state)

    # elif method == 'get_cost':
    #     if not activity_info.activities:
    #         return await get_account_data(event, state
    #
    #     scooter_id = activity_info.activities[0].bikeIdentifier
    #     value = activity_info.activities[0].bonusWithdrawnMoney.valueFormattedWithoutZero
    #     charge = int(float(activity_info.activities[0].charge.batteryPercent) * 100)
    #     print(scooter_id)
    #     print(value)
    #     print(charge)
    #     await call.answer(f'💰 Количество баллов на момент старта: {account_data.fake_points}\n'
    #                       f'💵 Стоимость поездки, с учетом суммы за старт: {value}\n'
    #                       f'🔋 Заряд самоката: {charge}%', show_alert=True)

    elif method == "select_card":
        if cards_info.entries:
            await call.answer('❌ Отвяжите привязанную карту, если вы хотите добавить новую', show_alert=True)
            return await get_account_data(call, state)

        cards_list = await cards_repository.getCardsByUserId(user_id=call.from_user.id)

        print(cards_list)

        payment_cards_paginator = PaymentCardsPaginator(account_id=account_data.id,
                                                        items=cards_list)

        return await call.message.edit_text(text=payment_cards_paginator.__str__(),
                                            reply_markup=payment_cards_paginator.generate_now_page())

    elif method == 'pay_card':
        if cards_info.entries:
            await call.answer('❌ Отвяжите привязанную карту, если вы хотите добавить новую', show_alert=True)
            return await get_account_data(call, state)

        card_id = int(list_call_data[2])
        card_data = await cards_repository.getCardByCardId(card_id)
        card_month, card_year = card_data.date.split('/')
        await call.message.edit_text(text='<b>💳 Начата привязка карты..</b>',
                                     reply_markup=generate_back_to_account_kb(account_id=account_data.id))

        yoomoney = True
        ecom_pay = False
        mts_pay = False

        if card_data.mts_pay and mts_pay:

            session_id, ssoTokenId = await urent_api.mtsPayAddCard()
            mts_pay_api = MtsPay(session_id=session_id, debug=True)
            response = await mts_pay_api.createPayment(ssoTokenId=ssoTokenId)
            zeon_api = ZeonAPI(port=228, debug=True)

            if response.get('PaReq'):
                response = await zeon_api.urent_payment_create_visa(payment_url=response['url'],
                                                                    pa_req=response['PaReq'],
                                                                    md=response['MD'],
                                                                    term_url=response['TermUrl'])
                json_response: dict = json.loads(response.text)
                confirmation_url = json_response.get('url')
            else:
                termUrlGet = response['confirm']['acsUrl']
                cReq = response['confirm']['cReq']
                print("termUrlGet", termUrlGet)
                print("cReq", cReq)
                print("MIR ECOM")
                response = await zeon_api.urent_payment_create_ecom_creq_mir(payment_url=termUrlGet,
                                                                             creq=cReq
                                                                             )
                json_response: dict = json.loads(response.text)
                confirmation_url = json_response.get('url')

            payment_kb, payment_text = generate_payment_kb(web_app=True,
                                                           payment_url=confirmation_url,
                                                           account_id=account_data.id,
                                                           payment_service='mts_pay',
                                                           card_id=card_data.id)

            return await call.message.edit_text(text=payment_text,
                                                reply_markup=payment_kb)

        elif card_data.yoomoney < 4 and yoomoney:

            try:
                response = await payment_api.yookassa_payment(pan=card_data.number,
                                                              csc=card_data.cvc,
                                                              expireDate='20' + card_year + card_month)
            except Exception as e:
                return await call.message.edit_text(
                    text='<b>🚫 Произошла ошибка при создании ссылки для проведения платежа, попробуйте еще раз</b>',
                    reply_markup=generate_back_to_account_kb(
                        account_id=account_data.id))

            if response.error is not None:
                return await call.message.edit_text(text=response.error,
                                                    reply_markup=generate_back_to_account_kb(
                                                        account_id=account_data.id))

            payment_kb, payment_text = generate_payment_kb(web_app=True,
                                                           payment_url=response.confirmation_url,
                                                           account_id=account_data.id,
                                                           payment_service='yoomoney',
                                                           card_id=card_data.id)

            return await call.message.edit_text(text=payment_text,
                                                reply_markup=payment_kb)

        elif card_data.ecom_pay < 4 and ecom_pay:
            response = await payment_api.ecom_pay_payment(pan=card_data.number,
                                                          expireDate=f'{card_month}/{card_year}',
                                                          csc=card_data.cvc)
            if response.error:
                return await call.message.edit_text(text=response.error,
                                                    reply_markup=generate_back_to_account_kb(
                                                        account_id=account_data.id))

            payment_kb, payment_text = generate_payment_kb(web_app=True,
                                                           payment_url=response.confirmation_url,
                                                           account_id=account_data.id,
                                                           payment_service='ecom_pay',
                                                           card_id=card_data.id)

            return await call.message.edit_text(text=payment_text,
                                                reply_markup=payment_kb)

        else:
            await cards_repository.banCardById(card_id=card_data.id)
            await call.message.edit_text(
                f'<b>❌ Карта уже использовалась максимальное количество раз, ожидайте ее разблокировки</b>',
                reply_markup=generate_back_to_account_kb(account_id=account_data.id))

    elif method == 'pay_card_mir':
        payment_url = await payment_api.link_card_mir()
        payment_kb, payment_text = generate_payment_kb(payment_url=payment_url,
                                                       account_id=account_data.id,
                                                       payment_service='mir_pay',
                                                       card_id=0)
        return await call.message.edit_text(text=payment_text,
                                            reply_markup=payment_kb)

    elif method == 'pay_card_tinkoff':
        payment_url_data = await payment_api.link_card_tinkoff()
        payment_id = payment_url_data.confirmationUrl.split('/')[-1]
        ios_payment_url = f'https://enotgo.ru/tpay?payment_id={payment_id}'
        payment_kb, payment_text = generate_payment_service_kb(android_payment_url=payment_url_data.confirmationUrl,
                                                               ios_payment_url=ios_payment_url,
                                                               account_id=account_data.id,
                                                               card_id=0,
                                                               payment_service='tinkoff_pay')
        return await call.message.edit_text(text=payment_text,
                                            reply_markup=payment_kb)

    elif method == 'pay_card_sb':
        payment_url_data = await payment_api.link_card_sberbank()
        parsed_url = parse.urlparse(payment_url_data.confirmationUrl)
        path_segments = parsed_url.query
        parsed_url = parse.parse_qs(path_segments)
        bankInvoiceId = parsed_url.get('bankInvoiceId', [''])[0]
        payment_id = parsed_url.get('payment_id', [''])[0]
        url_link = f"https://enotgo.ru/sberpay?payment_id={payment_id}&bankInvoiceId={bankInvoiceId}"
        payment_kb, payment_text = generate_payment_service_kb(android_payment_url=url_link,
                                                               ios_payment_url=url_link,
                                                               account_id=account_data.id,
                                                               card_id=0,
                                                               payment_service='sber_pay')
        return await call.message.edit_text(text=payment_text,
                                            reply_markup=payment_kb)

    elif method == 'check_payment':
        payment_service = list_call_data[2]
        card_id = int(list_call_data[3])

        if not cards_info.entries:
            return await call.answer('❌ Карта не была привязана, попробуйте выполнить процедуры заново',
                                     show_alert=True)

        if payment_service not in ['mir_pay', 'tinkoff_pay', 'sber_pay']:
            await cards_repository.usePaymentSystemByCardId(card_id=card_id, payment_system_id=payment_service)

        await call.answer('✅ Карта успешно привязана!', show_alert=True)
        return await get_account_data(call, state)

    elif method == "history_rides":
        response = await urent_api.get_orders()

        if response.errors:
            error = response.errors[0].value[0]
            return await call.answer(f'Ошибка при получении истории поездок: {error}', show_alert=True)

        all_receipts = []

        for ride in response.entries:
            all_receipts.append(ride)

        html_content = await generate_html_page(all_receipts, urent_api)
        html_bytes = html_content.encode('utf-8')
        html_file = BytesIO(html_bytes)
        zeon_api = ZeonAPI(port=300, debug=True)
        link_url = await zeon_api.urent_send_html_rides(phone_number=account_data.phone_number, html_file=html_file)
        await call.message.edit_text(
            text=f'<b>🟣 Нажмите на кнопку ниже для просмотра поездок на аккаунте\n'
                 f'📞 Номер телефона: <code>{account_data.phone_number}</code></b>',
            reply_markup=generate_history_url(link_url=link_url, account_id=account_data.id))


@account_router.callback_query(F.data.startswith(("get_account")))
async def get_account_data(event: CallbackQuery | Message, state: FSMContext):
    # Получение данных аккаунта
    if isinstance(event, CallbackQuery):
        account_id = int(event.data.split(':')[1])
        account_data = await account_repository.getAccountByAccountId(account_id=account_id)
    else:
        state_data = await state.get_data()
        await state.clear()
        coupon = event.text
        event: CallbackQuery = state_data['call']
        account_data = await account_repository.getAccountByCoupon(coupon=coupon)

    if not account_data:
        return await event.message.edit_text(f"<b>❌ Ошибка: аккаунт не найден</b>")

    # Проверка удаления аккаунта и прав доступа
    if account_data.is_deleted and event.from_user.id not in ADMIN_LIST:
        return await event.message.edit_text(
            f"<b>❌ Ошибка: аккаунт удален\n"
            f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
            f"🎫 Купон: <code>{account_data.coupon}</code></b>")

    try:
        await event.message.edit_text('<b>⌛ Происходит загрузка аккаунта. Ожидайте..</b>')
    except Exception as e:
        print(traceback.format_exc())

    # Получение данных через UrentAPI
    urent_api = UrentAPI(refresh_token=account_data.refresh_token, access_token=account_data.access_token)
    payment_profile = await urent_api.get_payment_profile()

    # Проверка истечения refresh_token
    if payment_profile.wrong_refresh_token:
        return await event.message.answer(
            text=f"❌ <b>Ошибка: Токен обновления устарел\n"
                 f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                 f"🎫 Купон: <code>{account_data.coupon}</code></b>",
            reply_markup=generate_go_to_support_kb()
        )

    # # Получение дополнительных данных с измерением времени
    # start_time = time.time()  # Зафиксировать время начала

    activity_info, plus_info, cards_info, promo_actions = await asyncio.gather(
        urent_api.get_activity(),
        urent_api.get_plus_info(),
        urent_api.get_cards(),
        urent_api.get_promo_actions()
    )

    # end_time = time.time()  # Зафиксировать время окончания
    #
    # # Подсчет и вывод времени, затраченного на запросы
    # execution_time = end_time - start_time
    # print(f"Время, потраченное на выполнение запросов: {execution_time:.4f} секунд")
    #

    cards_id = [card.id for card in cards_info.entries]

    # Обновление статуса, если токен некорректный
    if account_data.wrong_refresh_token:
        await account_repository.updateAccountStatusWrongActivationPromoByAccountId(
            account_id=account_data.id, wrong_activation_promo=False
        )

    # Обновление статуса привязки карты
    if not account_data.is_card_linked and payment_profile.cards:
        await account_repository.updateAccountIsCardLinkedByAccountId(account_id=account_data.id)

    elif account_data.is_card_linked and not payment_profile.cards:
        await account_repository.updateAccountIsCardLinkedByAccountId(account_id=account_data.id,
                                                                      is_card_linked=False)

    # Обновление статуса промокода
    if not account_data.is_promo_code_activated and any([account_data.promo_code == promo_code_data for promo_code_data in payment_profile.promoCodes]):
        await account_repository.updateAccountIsPromoCodeActivatedByAccountId(account_id=account_data.id)

    # Проверка функциональности аккаунта
    if account_data.account_functionality == 0 and payment_profile.bonuses.value > 0:
        await event.message.edit_text(
            text=f"✅ <b>Спасибо, что пользуетесь нашим сервисом, напишите саппорту для получение аккаунта\n"
                 f"Все привязанные карты уже были удалены с вашего аккаунта"
                 f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                 f"🎫 Купон: <code>{account_data.coupon}</code></b>",
            reply_markup=generate_go_to_support_kb()
        )

        # Удаление привязанных карт и сброс купона

        await asyncio.gather(*(urent_api.remove_card(card_id=card_id) for card_id in cards_id))

        orders = await urent_api.get_orders()
        coupon = await account_repository.resetAccountByAccountId(account_id=account_data.id, change_coupon=True)

        # Обновление аккаунта после сброса купона
        if coupon:
            account_data = await account_repository.getAccountByAccountId(account_id=account_data.id)

        functionality = 2 if not payment_profile.promoCodes and account_data.promo_code and not orders.entries else 1
        await account_repository.updateAccountFunctionalityByAccountId(account_id=account_data.id,
                                                                       account_functionality=functionality)

        filename = f'{functionality} {bool(account_data.ya_token)} {payment_profile.bonuses.value}.txt'
        async with aiofiles.open(filename, mode='a') as balance_file:
            await balance_file.write(f'{account_data.coupon}\n')

    # Обновление фейковых поинтов
    if not activity_info.activities and payment_profile.promoCodes:
        await account_repository.updateAccountFakePointsByAccountId(account_id=account_data.id,
                                                                    points=payment_profile.bonuses.value)

    # Попытка активации промокода, если возможно
    if (
            cards_info.entries and not payment_profile.promoCodes and not activity_info.activities and
            account_data.promo_code and account_data.account_functionality in [0,
                                                                               2] and not account_data.wrong_activation_promo
    ):
        promo_code = account_data.promo_code
        response = await urent_api.activate_promo_code(promo_code)

        if response.errors and response.errors[0].value[0].startswith(
                ('Вам недоступно использование промокодов', 'Этот промокод уже все. Не работает', 'Промокод не найден')
        ):
            error = response.errors[0].value[0]

            await bot_logger.send_message(
                chat_id=CHANNEL_ID, text=f"❌ <b>Ошибка: {error}\n"
                                         f"☠️ Промокод: <code>{promo_code}</code>\n"
                                         f"📞 Номер телефона: <code>{account_data.phone_number}</code>\n"
                                         f"💰 Количество баллов на аккаунте: <code>{payment_profile.bonuses.value}</code>\n"
                                         f"🎫 Купон: <code>{account_data.coupon}</code>\n"
                                         f"💜 Пользователь: @{event.from_user.username}</b>"
            )

            linked_card_number = cards_info.entries[0].cardNumber
            user_cards_list = await cards_repository.getCardsByUserId(user_id=account_data.user_id)

            if error.startswith('Вам недоступно использование промокодов'):

                await asyncio.gather(
                    *(cards_repository.banCardById(card_id=user_card.id) for user_card in user_cards_list if
                      user_card.number.endswith(linked_card_number[-4:])))

                if account_data.account_functionality == 0:
                    await asyncio.gather(*(urent_api.remove_card(card_id=card_id) for card_id in cards_id))

            await account_repository.updateAccountStatusWrongActivationPromoByAccountId(account_id=account_data.id)

            if payment_profile.bonuses.value <= 0:
                await account_repository.updateAccountIsDeletedStatusByAccountId(account_id=account_data.id)
                return await event.message.edit_text(
                    text=f'<b>❌ Ошибка: Аккаунт был заблокирован\n'
                         f'📞 Номер телефона: <code>{account_data.phone_number}</code>\n'
                         f'🎫 Купон: <code>{account_data.coupon}</code></b>',
                    reply_markup=generate_go_to_support_kb()
                )

            elif account_data.account_functionality == 2:
                await account_repository.updateAccountFunctionalityByAccountId(account_id=account_data.id,
                                                                               account_functionality=1)

        return await get_account_data(event, state)

    # Получение данных поездки, если есть активности
    ride = await rides_repository.get_ride_by_rate_id(
        rate_id=activity_info.activities[0].rateId) if activity_info.activities else None

    # Генерация и отправка информации об аккаунте
    account_kb, account_info = generate_account_kb(
        account_data=account_data,
        payment_profile=payment_profile,
        activity_info=activity_info,
        cards_info=cards_info,
        promo_actions=promo_actions,
        ride=ride,
        plus_info=plus_info,
        admin_keyboard=event.from_user.id in ADMIN_LIST
    )
    await event.message.edit_text(text=account_info, reply_markup=account_kb, disable_web_page_preview=True)


@account_router.callback_query(F.data.startswith(('off_auto_stop', 'on_auto_stop')))
async def off_auto_stop_callback_query(call: CallbackQuery):
    scooter_kb = InlineKeyboardBuilder()
    for inline_button in call.message.reply_markup.inline_keyboard:
        if inline_button[0].callback_data == 'off_auto_stop':
            scooter_kb.row(InlineKeyboardButton(text='✅ Включить автозавершение',
                                                callback_data='on_auto_stop'))
            continue
        elif inline_button[0].callback_data == 'on_auto_stop':
            scooter_kb.row(InlineKeyboardButton(text='⛔ Отключить автозавершение',
                                                callback_data='off_auto_stop'))
            continue
        scooter_kb.row(InlineKeyboardButton(text=inline_button[0].text,
                                            callback_data=inline_button[0].callback_data))

    await call.message.edit_reply_markup(reply_markup=scooter_kb.as_markup())


@account_router.message(UserStates.input_scooter)
async def start_drive(message: Message, state: FSMContext, bot: Bot):
    await message.delete()
    scooter_id = ''.join([char for char in message.text.split('-') if char.isdigit()])
    data = await state.get_data()
    account_data: Accounts = data['account_data']
    cancel_message: CallbackQuery = data['cancel_message']
    await state.clear()
    if scooter_id == '':
        return await cancel_message.message.edit_text(text=f"<b>❌ Введите правильно номер самоката</b>",
                                                      reply_markup=generate_back_to_account_kb(
                                                          account_id=account_data.id))
    scooter_id = f'S.{scooter_id}'
    account_data = await account_repository.getAccountByAccountId(account_data.id)
    refresh_token = account_data.refresh_token
    access_token = account_data.access_token
    urent_api = UrentAPI(refresh_token=refresh_token,
                         access_token=access_token)

    scooter_info = await urent_api.get_scooter_info(transport=scooter_id)
    if scooter_info.errors:
        return await cancel_message.message.edit_text(text=f"❌ <b>Ошибка: {scooter_info.errors[0].value[0]}</b>",
                                                      reply_markup=generate_back_to_account_kb(
                                                          account_id=account_data.id))

    RATE_KEYBOARD = InlineKeyboardBuilder()
    RATE_KEYBOARD.row(InlineKeyboardButton(text="⛔ Отключить автозавершение", callback_data="off_auto_stop"))

    ############

    charge = f"{int(scooter_info.charge.batteryPercent * 100)}%"

    verify_cost = scooter_info.rate.verifyCost.valueFormatted

    battery_for_active_in_hours = str(int(scooter_info.charge.batteryForActiveInHours * 60)) + ' мин.'
    lat = scooter_info.location.lat
    lng = scooter_info.location.lng

    plus_info = await urent_api.get_plus_info()

    geolocation_info = await urent_api.get_geolocation(lat=lat, lng=lng)

    display_name = scooter_info.rate.displayName

    promo_actions = await urent_api.get_promo_actions()
    payment_profile = await urent_api.get_payment_profile()

    debit_value = scooter_info.rate.debit.value
    account_points = payment_profile.bonuses.value

    if plus_info.entries:
        activation_cost = 0

    elif scooter_info.rate.activationCost:
        activation_cost = scooter_info.rate.activationCost.value
    else:
        activation_cost = 0

    if account_data.account_functionality == 0 and promo_actions.entries:
        discount_percentage = promo_actions.entries[0].discountPercentage
        unused_amount = promo_actions.entries[0].unusedAmount.value
        max_amount_with_discount = (unused_amount * (1 + (discount_percentage / 100)) - activation_cost)

        if promo_actions.entries[0].unusedTrips > 1:
            time_in_minutes = min(max_amount_with_discount / debit_value, 200 / debit_value)

        else:
            time_in_minutes = max_amount_with_discount / debit_value

    elif account_data.account_functionality == 1:
        time_in_minutes = (account_points - activation_cost) / debit_value

    elif account_data.account_functionality == 2:
        if not promo_actions.entries:
            time_in_minutes = (account_points - activation_cost) / debit_value
        else:
            discount_percentage = promo_actions.entries[0].discountPercentage
            unused_amount = promo_actions.entries[0].unusedAmount.value

            discount_time_in_minutes = (unused_amount * (
                    1 + (discount_percentage / 100)) - activation_cost) / debit_value

            points_time_in_minutes = (account_points * (
                    1 + (discount_percentage / 100)) - activation_cost) / debit_value

            time_in_minutes = min(discount_time_in_minutes, points_time_in_minutes)

    else:
        time_in_minutes = 0

    scooter_text = (f'🛴 <b>Номер самоката:</b> <i>{scooter_id}</i>\n'
                    f'💵 <b>Стоимость залога:</b> <i>{verify_cost}</i>\n'
                    f'🔋 <b>Заряд самоката:</b> <i>{charge}</i>\n'
                    f'⏳ <b>На сколько хватит заряда:</b> <i>{battery_for_active_in_hours} | {round(scooter_info.charge.remainKm, 2)} км</i>\n'
                    f'📌 <b>Название самоката:</b> <i>{scooter_info.modelName}</i>\n'
                    f'🏙️ <b>Город:</b> <i>{geolocation_info.cityName}</i>\n'
                    f'\n'
                    f'⚠️ <b><i>Поездка автоматически завершится через {int(time_in_minutes)} мин.</i></b>\n'
                    f'<b><a href="{HELP_URL}">✏️ Что такое авто-завершение?</a></b>\n'
                    )

    cost = scooter_info.rate.debit.valueFormatted
    id_tariff = scooter_info.rate.id

    RATE_KEYBOARD.row(InlineKeyboardButton(text="⭐ Забронировать самокат",
                                           callback_data=f"booking_make:{account_data.id}:{scooter_id}"))

    RATE_KEYBOARD.row(InlineKeyboardButton(text=f'🟣 {display_name} | {activation_cost} + {cost}',
                                           callback_data=f'start_tariff:{account_data.id}:{id_tariff}:{scooter_id}'))

    RATE_KEYBOARD.row(InlineKeyboardButton(text="↪️ Вернуться в аккаунт",
                                           callback_data=f"get_account:{account_data.id}"))

    try:
        await cancel_message.message.edit_text(text=scooter_text,
                                               reply_markup=RATE_KEYBOARD.as_markup(),
                                               disable_web_page_preview=True)
    except Exception:
        await message.answer(text=scooter_text,
                             reply_markup=RATE_KEYBOARD.as_markup(),
                             disable_web_page_preview=True)
