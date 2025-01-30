# -*- coding: utf-8 -*-
from datetime import datetime

from aiogram.types import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from api import UrentAPI
from api.urent.models import ActivityModel, CardsModel, PaymentProfileModel, OrdersModel, PromoActionsModel, \
    PlusInfoModel
from db.models import Users, Accounts, Rides, Cards
from settings import HELP_URL, HELP_TG


def generate_go_to_support_kb() -> InlineKeyboardMarkup:
    help_menu = InlineKeyboardBuilder()
    help_menu.row(InlineKeyboardButton(text='🟣 Написать саппорту', url=HELP_TG))
    return help_menu.as_markup()


def generate_help_kb() -> InlineKeyboardMarkup:
    help_menu = InlineKeyboardBuilder()
    help_menu.row(InlineKeyboardButton(text='💬 Инструкция', url=HELP_URL))
    help_menu.row(InlineKeyboardButton(text='🟣 Написать саппорту', url=HELP_TG))
    return help_menu.as_markup()


def generate_admin_menu_kb() -> InlineKeyboardMarkup:
    admin_menu = InlineKeyboardBuilder()
    admin_menu.row(InlineKeyboardButton(text='📱 Управление аккаунтом', callback_data='account_management'))
    admin_menu.row(InlineKeyboardButton(text='💳 Управление картой', callback_data='card_management'))
    admin_menu.row(InlineKeyboardButton(text='👽 Управление пользователем', callback_data='user_management'))
    admin_menu.row(InlineKeyboardButton(text="❌ Отменить действие", callback_data="cancel"))
    return admin_menu.as_markup()


def generate_main_menu_kb() -> ReplyKeyboardMarkup:
    MAIN_MENU = ReplyKeyboardBuilder()
    MAIN_MENU.row(KeyboardButton(text='🔑 Ввести ключик'))
    MAIN_MENU.row(KeyboardButton(text='ℹ️ Личный кабинет'))
    MAIN_MENU.row(KeyboardButton(text='💬 Помощь'))
    MAIN_MENU.row(KeyboardButton(text='🎁 Получить подарок'))
    return MAIN_MENU.as_markup(resize_keyboard=True)


def generate_inline_main_menu() -> InlineKeyboardMarkup:
    MAIN_MENU = InlineKeyboardBuilder()
    MAIN_MENU.row(InlineKeyboardButton(text='💬 Инструкция для новых пользователей', url=HELP_URL))
    return MAIN_MENU.as_markup()


def generate_personal_area_kb() -> InlineKeyboardMarkup:
    personal_area_kb = InlineKeyboardBuilder()
    personal_area_kb.row(
        InlineKeyboardButton(text="📋 История активаций", callback_data="history_paginator:send_menu:1"))
    personal_area_kb.row(InlineKeyboardButton(text="📱 Мои аккаунты", callback_data="account_paginator:send_menu:1"))
    personal_area_kb.row(InlineKeyboardButton(text='💳 Мои карты', callback_data="cards_paginator:send_menu:1"))
    return personal_area_kb.as_markup()


def generate_cancel_kb() -> InlineKeyboardMarkup:
    CANCEL_KEYBOARD = InlineKeyboardBuilder()
    CANCEL_KEYBOARD.add(InlineKeyboardButton(text="❌ Отменить действие", callback_data="cancel"))
    return CANCEL_KEYBOARD.as_markup()


def generate_get_account_kb_by_id(account_id: int) -> InlineKeyboardMarkup:
    """
    _id: account id from Account class
    """
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='↪️ Перейти к аккаунту',
                                      callback_data=f'get_account:{account_id}'))
    return keyboard.as_markup()


def generate_delete_account_kb(account_id: int) -> InlineKeyboardMarkup:
    kb_delete_to_acc = InlineKeyboardBuilder()
    kb_delete_to_acc.add(InlineKeyboardButton(text='✅ Подтвердить действие',
                                              callback_data=f'accept_remove_acc:{account_id}'))
    kb_delete_to_acc.add(InlineKeyboardButton(text='❌ Отменить действие',
                                              callback_data=f'get_account:{account_id}'))
    return kb_delete_to_acc.as_markup()


def generate_back_to_account_kb(account_id: int | str) -> InlineKeyboardMarkup:
    kb_back_to_acc = InlineKeyboardBuilder()
    kb_back_to_acc.add(InlineKeyboardButton(text='↪️ Вернуться в аккаунт',
                                            callback_data=f"get_account:{account_id}"))
    return kb_back_to_acc.as_markup()


def generate_account_kb(account_data: Accounts,
                        activity_info: ActivityModel.Activity,
                        cards_info: CardsModel.Cards,
                        payment_profile: PaymentProfileModel.PaymentProfile,
                        promo_actions: PromoActionsModel.PromoActions,
                        ride: Rides,
                        plus_info: 'PlusInfoModel.PlusInfo',
                        admin_keyboard=False,
                        ) -> tuple[InlineKeyboardMarkup, str]:
    account_menu = InlineKeyboardBuilder()
    if cards_info.entries and not activity_info.activities:
        account_menu.row(InlineKeyboardButton(text='⚡️ Начать поездку', callback_data=f"start_drive:{account_data.id}"))

    if cards_info.entries and activity_info.activities and activity_info.activities[0].status == 'Booking':
        account_menu.row(InlineKeyboardButton(text="🔔 Поиск самоката", callback_data=f"find_scooter:{account_data.id}"))
        account_menu.row(
            InlineKeyboardButton(text="🚫 Отменить бронь самоката", callback_data=f"booking_cancel:{account_data.id}"))

    if activity_info.activities and activity_info.activities[0].status in ['Ordered', "Closing", "Waiting"]:
        account_menu.row(
            InlineKeyboardButton(text='❌ Завершить поездку', callback_data=f"stop_drive:{account_data.id}"))

        if activity_info.activities[0].status == 'Waiting':
            account_menu.row(
                InlineKeyboardButton(text='▶️ Снять с паузы', callback_data=f"remove_pause_drive:{account_data.id}"))

        if activity_info.activities[0].status == 'Ordered':
            account_menu.row(
                InlineKeyboardButton(text='⏸ Поставить на паузу', callback_data=f"pause_drive:{account_data.id}"))


    if not activity_info.activities and not cards_info.entries:
        account_menu.row(InlineKeyboardButton(text='💳 Привязать карту', callback_data=f"select_card:{account_data.id}"))

    if not activity_info.activities and cards_info.entries:
        account_menu.row(InlineKeyboardButton(text='💳 Отвязать карты', callback_data=f"remove_cards:{account_data.id}"))

    if not activity_info.activities:
        account_menu.row(
            InlineKeyboardButton(text="🕒 История поездок", callback_data=f"history_rides:{account_data.id}"))

    if not activity_info.activities and not plus_info.entries and account_data.ya_token:
        account_menu.row(InlineKeyboardButton(text='🔥 Активировать бесплатный старт 🔥',
                                              callback_data=f"activate_free_start:{account_data.id}"))

    # if cards_info.entries and not activity_info.activities:
    #     account_menu.row(InlineKeyboardButton(text='🧷 Активировать промокод',
    #                                           callback_data=f"activate_promo_code:{account_data.id}"))

    account_menu.row(InlineKeyboardButton(text='♻️ Обновить сведения', callback_data=f"get_account:{account_data.id}"))

    if not cards_info.entries and not activity_info.activities:
        account_menu.row(InlineKeyboardButton(text='❌ Удалить аккаунт', callback_data=f'remove_acc:{account_data.id}'))

    if admin_keyboard:
        if account_data.is_deleted:
            account_menu.row(
                InlineKeyboardButton(text='✅ Восстановить аккаунт', callback_data=f'recover_account:{account_data.id}'))

        if account_data.user_id:
            account_menu.row(
                InlineKeyboardButton(text='♾ Сбросить аккаунт', callback_data=f'reset_activation:{account_data.id}'))

    account_menu.row(
        InlineKeyboardButton(text='↪️ Назад в список аккаунтов', callback_data=f"account_paginator:send_menu:1"))

    account_menu_text = f'<b>📱 Номер телефона: <code>{account_data.phone_number}</code></b>\n' \
                        f'<b>🔑 Использованный ключ: <code>{account_data.coupon}</code></b>\n'

    if activity_info.activities:
        account_menu_text += f'<b>🛴 Номер самоката: <code>{activity_info.activities[0].bikeIdentifier}</code></b>\n'
        account_menu_text += f'<b>💰 Количество баллов на момент старта: <code>{account_data.fake_points}</code></b>\n'
        account_menu_text += f'<b>💵 Стоимость поездки, с учетом суммы за старт: <code>{activity_info.activities[0].bonusWithdrawnMoney.valueFormattedWithoutZero}</code></b>\n'
        account_menu_text += f'<b>🔋 Заряд самоката: <code>{int(float(activity_info.activities[0].charge.batteryPercent) * 100)}%</code></b>\n'

    last_purchase_date = payment_profile.lastPurchase.dateTimeUtc

    if last_purchase_date:
        date_obj = datetime.fromisoformat(last_purchase_date.replace("Z", "+00:00"))
        last_purchase_date = date_obj.strftime("%d/%m/%Y, %H:%M:%S")

    if not activity_info.activities and account_data.account_functionality in [1, 2]:
        account_menu_text += f'<b>🟣 Количество баллов на аккаунте: <code>{payment_profile.bonuses.value}</code></b>\n'

    if not activity_info.activities and account_data.account_functionality in [0, 2]:
        account_menu_text += '<b>🟣 Информация о скидке:\n</b>'
        if any(account_data.promo_code == promo_code_data.code for promo_code_data in payment_profile.promoCodes) and not promo_actions.entries:
            account_menu_text += f"     └ <b>Количество оставшихся поездок со скидкой: <code>{0}</code></b>\n"

        elif promo_actions.entries:
            account_menu_text += f"     └ <b>Скидка: <code>{promo_actions.entries[0].discountPercentage}%</code></b>\n"
            account_menu_text += f"     └ <b>Остаточная сумма скидки: <code>{promo_actions.entries[0].unusedAmount.value}</code></b>\n"
            account_menu_text += f"     └ <b>Количество оставшихся поездок со скидкой: <code>{promo_actions.entries[0].unusedTrips}</code></b>\n"

        else:
            account_menu_text += f"     └ <b>Количество оставшихся поездок со скидкой: <code>{account_data.fake_free_rides}</code></b>\n"

    # registration_date = account_data.creation_date.strftime("%d/%m/%Y, %H:%M:%S")
    if not activity_info.activities:
        account_menu_text += (
        f'<b>💳 Привязанная карта: <i>{"Нет" if not cards_info.entries else cards_info.entries[0].cardNumber}</i></b>\n'
        f'<b>📝 Последняя транзакция: <i>{last_purchase_date} | {payment_profile.lastPurchase.amount.valueFormatted if payment_profile.lastPurchase.amount is not None else None}</i></b>\n'
        # f'<b>📅 Дата регистрации аккаунта: <i>{registration_date}</i></b>\n'
        # f'<b><a href="https://teletype.in/@shadow1ch/mts_premium">🎵 Как подключить бесплатный старт на свой аккаунт?</a>'
        f'</b>\n')

    if ride and datetime.utcnow() < ride.finished_time:
        end_date = ride.finished_time.strftime("%d/%m/%Y, %H:%M:%S")
        account_menu_text += f'<b>🏁 Поездка автоматически завершится: <i>{end_date}</i></b>\n'

    if activity_info.activities:
        account_menu_text += f'<b><i>ℹ️ Для того, чтобы увидеть обновленную информацию о поездке нажмите на "Обновить сведения"</i></b>'

    return account_menu.as_markup(), account_menu_text


def generate_payment_kb(payment_url: str,
                        account_id: str | int,
                        card_id: int | None,
                        payment_service: str,
                        web_app=False) -> tuple[InlineKeyboardMarkup, str]:
    """
    payment_service: mir_pay or yoomoney, ecom_pay
    """
    payment_kb = InlineKeyboardBuilder()
    if web_app:
        payment_kb.row(InlineKeyboardButton(text='💵 Оплата', web_app=WebAppInfo(url=payment_url)))
    else:
        payment_kb.row(InlineKeyboardButton(text='💵 Оплата', url=payment_url))

    payment_kb.row(InlineKeyboardButton(text='✅ Проверить оплату',
                                        callback_data=f'check_payment:{account_id}:{payment_service}:{card_id}'))

    # payment_kb.row(InlineKeyboardButton(text='↪️ Вернуться в аккаунт', callback_data=f'get_account:{__account_id}'))

    return payment_kb.as_markup(), ('<b>🟣 Нажмите на кнопку ниже для привязки карты к аккаунту:</b>')


def generate_payment_service_kb(
        android_payment_url: str,
        ios_payment_url: str,
        account_id: str | int,
        card_id: str | int | None,
        payment_service: str,
) -> tuple[InlineKeyboardMarkup, str]:
    payment_kb, kb_text = InlineKeyboardBuilder(), '<b>🟣 Нажмите на кнопку ниже для привязки карты к аккаунту:</b>\n\n'
    payment_kb.row(InlineKeyboardButton(text='👽 Android', url=android_payment_url))
    payment_kb.row(InlineKeyboardButton(text='🍏 IOS', url=ios_payment_url))

    payment_kb.row(InlineKeyboardButton(text='✅ Проверить оплату',
                                        callback_data=f'check_payment:{account_id}:{payment_service}:{card_id}'))

    # payment_kb.row(InlineKeyboardButton(text='↪️ Вернуться в аккаунт', callback_data=f'get_account:{account_id}'))

    if payment_service == 'sber_pay':
        kb_text += ('<b>⚠️ Если у вас <u>SberKids</u>, данный способ привязки не будет работать ⚠️\n'
                    '⚠️ Если у вас <u>IOS</u> - открывайте ссылку через браузер <u>Safari</u> ⚠️</b>')

    elif payment_service == 'tinkoff_pay':
        kb_text += '<b>⚠️ Если у вас <u>IOS</u> - открывайте ссылку через браузер <u>Safari</u></b> ⚠️'

    return payment_kb.as_markup(), kb_text


async def generate_trip_html(trip: OrdersModel.Entry, urent_api: UrentAPI):
    trip_index = trip.id
    start_date_time = trip.startDateTimeUtc
    end_date_time = trip.endDateTimeUtc
    bike_identifier = trip.bikeIdentifier
    costcard = trip.personalWithdrawnMoney.valueFormatted
    cost = trip.summaryWithdrawn.valueFormatted
    rate_name = trip.rateName
    amountdrive = trip.withdrawal.withdrawals[2].amount.valueFormatted
    rate_value = trip.rate.valueFormatted
    activation_cost = trip.activation.valueFormatted
    elapsed_seconds = trip.statistics.elapsedSeconds
    insurance_cost = trip.insurance.valueFormatted
    bonus_cost = trip.bonusWithdrawnMoney.valueFormatted
    track = trip.track
    startBikeLocationLat = trip.startBikeLocation.lat
    startBikeLocationLng = trip.startBikeLocation.lng
    download_receipt = await urent_api.get_ride_payment_info(ride_id=trip.id)
    if download_receipt.receipts:
        download_receipt = download_receipt.receipts[0]
    else:
        download_receipt = "Fail"
    # Форматирование даты
    formatted_start_date_time = format_date(start_date_time)
    formatted_end_date_time = format_date(end_date_time)

    # Вычисление времени поездки в формате "часы:минуты"
    elapsed_hours = int(elapsed_seconds // 60)
    elapsed_minutes = int(elapsed_seconds % 60)
    formatted_elapsed_time = f"{elapsed_hours:02}:{elapsed_minutes:02}"
    coordinates = []
    for point in track:
        coordinates.append([point.lng, point.lat])
    trip_html = f"""
    <div class="trip">
        <div class="trip-button">
            <div class="map-container" style="border-radius: 10px; overflow: hidden; margin-bottom: 20px;">
                <div id="map-container-{trip_index}" style="height: 250px;"></div>
                <script src="https://mapgl.2gis.com/api/js/v1"></script>
                <script>
                    const map{trip_index} = new mapgl.Map('map-container-{trip_index}', {{
                        center: [{startBikeLocationLng}, {startBikeLocationLat}], // координаты центра карты (широта, долгота)
                        zoom: 15, // масштаб карты
                        key: '82de0e80-2b53-4d04-b5e8-065a25ccab00', // ваш ключ API
                        style: 'c080bb6a-8134-4993-93a1-5b4d8c36a59b' // стиль карты
                    }});
                    const polyline{trip_index} = new mapgl.Polyline(map{trip_index}, {{
                        coordinates: 
                            {coordinates},
                        width: 10,
                        color: '#6a5acd',
                    }});
                </script>
            </div>
            <button class="trip-button" onclick="toggleDetails(this)">
                <div class="trip-summary">
                    <img src="https://www.svgrepo.com/show/104543/micro-scooter.svg" alt="Scooter Icon" class="scooter-icon">
                    <div class="trip-info">
                        <div class="trip-date">{formatted_start_date_time}</div>
                        <div class="trip-id">{bike_identifier}</div>
                    </div>
                    <div class="trip-cost">{cost}</div>
                </div>
            </button>
            <div class="trip-details" style="display: none;">
                <div class="info-section">
                    <div class="info-header">Поездка</div>
                    <div class="info-row">
                        <div class="info-label">Старт</div>
                        <div class="info-value">{formatted_start_date_time.split()[4]}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Завершение</div>
                        <div class="info-value">{formatted_end_date_time.split()[4]}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">В пути</div>
                        <div class="info-value">{formatted_elapsed_time}</div>
                    </div>
                    <hr class="info-divider">
                </div>
                <div class="cost-section">
                    <div class="info-header">Стоимость</div>
                    <div class="cost-row">
                        <div class="cost-label">Тариф (Поминутный)</div>
                        <div class="cost-value"></div>
                        <div class="cost-right">{rate_value}</div>
                    </div>
                    <div class="cost-row">
                        <div class="cost-label">Стоимость старта</div>
                        <div class="cost-value"></div>
                        <div class="cost-right">{activation_cost}</div>
                    </div>
                    <div class="cost-row">
                        <div class="cost-label">Стоимость поездки</div>
                        <div class="cost-value"></div>
                        <div class="cost-right">{amountdrive}</div>
                    </div>
                    <div class="cost-row">
                    </div>
                    <div class="cost-row">
                        <div class="cost-label-itog">Итого</div>
                        <div class="cost-value"></div>
                        <div class="cost-right-itog">{cost}</div>
                    </div>
                    <hr class="cost-divider">
                    <div class="cost-row">
                        <div class="cost-label">Оплачено бонусами</div>
                        <div class="cost-value"></div>
                        <div class="cost-right">{bonus_cost}</div>
                    </div>
                    <div class="cost-row">
                        <div class="cost-label">Оплачено картой</div>
                        <div class="cost-value"></div>
                        <div class="cost-right">{costcard}</div>
                    </div>
                    <hr class="cost-divider">
                </div>
            <div style="text-align: center; margin-top: 20px;"> <!-- Обертка для центрирования -->
                <a class="download-button" href="#" onclick="downloadReceipt('{download_receipt}')">Скачать чек</a>
            </div>
            </div>
        </div>
    </div>
    <script>
        function downloadReceipt(check) {{
            if (check === 'Fail') {{
            }} else {{
                window.open(check, '_blank');
            }}
        }}
    </script>
    """
    return trip_html


async def generate_html_page(all_receipts: list[OrdersModel.Entry], urent_api: UrentAPI):
    trips_html = []
    for index, trip in enumerate(all_receipts):
        trip_html = await generate_trip_html(trip, urent_api)
        trips_html.append(trip_html)
    all_trips_html = '\n'.join(trips_html)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Trips History</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f7f7f7;
            }}
            .container {{
                max-width: 800px;
                margin: 20px auto;
                padding: 20px;
                background-color: #fff;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            .trip {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-bottom: 1px solid #ccc;
                padding: 10px 0;
            }}
            .trip-button {{
                border: none;
                background-color: #fff;
                color: #000;
                cursor: pointer;
                outline: none;
                width: 100%;
                text-align: left;
                padding: 10px 20px;
                border-radius: 20px;
                box-shadow: 0 5px 5px rgba(0, 0, 0, 0.1);
                transition: background-color 0.3s;
                -webkit-tap-highlight-color: transparent;
            }}
            .trip-button:hover {{
                background-color: #f0f0f0;
            }}
            .trip-button:hover .trip-summary {{
                background-color: transparent;
            }}
            .trip-summary {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                width: 100%;
            }}
            .scooter-icon {{
                width: 20px;
                height: 20px;
                margin-right: 10px;
            }}
            .trip-info {{
                margin-right: 20px;
            }}
            .trip-date {{
                font-size: 18px;
                font-weight: bold;
            }}
            .trip-id {{
                font-size: 16px;
                margin-top: 5px;
            }}
            .trip-cost {{
                font-size: 20px;
                font-weight: bold;
                white-space: nowrap;
            }}
            .trip-details {{
                display: none;
                width: 100%;
                margin-top: 10px;
                margin-left: -10px;
                padding: 10px;
                border-radius: 10px;
                box-shadow: 0 5px 5px rgba(0, 0, 0, 0.1);
                background-color: #f7f7f7;
            }}
            .trip-details .info-section {{
                margin-bottom: 20px;
            }}
            .info-header {{
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .info-row, .cost-row {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 5px;
            }}
            .info-divider, .cost-divider {{
                border: none;
                border-top: 1px solid #ccc;
                margin: 10px 0;
            }}
            .info-label, .cost-label, .info-value, .cost-value, .cost-right {{
                font-size: 15px;
            }}

            .info-label-itog, .cost-label-itog {{
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .cost-right {{
                text-align: right;
            }}
            .cost-right-itog {{
                font-weight: bold;
                text-align: right;
            }}
            .download-button {{
                border: 2px solid #6a5acd;
                background-color: #ffffff;
                color: #6a5acd;
                cursor: pointer;
                outline: none;
                padding: 10px 20px;
                border-radius: 15px;
                font-size: 16px;
                transition: background-color 0.3s, color 0.3s, border-color 0.3s;
                display: inline-block;
                text-decoration: none;
            }}
            .download-button:hover {{
                background-color: #6a5acd; /* Фон становится фиолетовым при наведении */
                color: #ffffff; /* Текст становится белым при наведении */
                border-color: #6a5acd; /* Цвет рамки меняется на фиолетовый при наведении */
            }}
        </style>
        <script>
    function toggleDetails(button) {{
        var details = button.parentElement.querySelector('.trip-details');
        details.style.display = details.style.display === 'none' ? 'block' : 'none';
    }}
</script>

    </head>
    <body>
        <div class="container">
            <h1>История поездок</h1>
            {all_trips_html}
        </div>
    </body>
    </html>
    """
    return html_content


def format_date(date_str: str):
    from datetime import datetime
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября",
              "декабря"]
    date_parts = date_str.split("T")[0].split("-")
    year = date_parts[0]
    month = months[int(date_parts[1]) - 1]
    day = date_parts[2]
    time_str = date_str.split("T")[1]
    time_str: str = time_str.split('.')[0]
    time = datetime.strptime(time_str, "%H:%M:%S")

    return f"{day} {month} {year} г. {time.strftime('%H:%M')}"


def generate_history_url(link_url: str, account_id: str | int):
    HISTORY_KEYBOARD = InlineKeyboardBuilder()
    HISTORY_KEYBOARD.row(InlineKeyboardButton(text="📋 История поездок", web_app=WebAppInfo(url=link_url)))
    HISTORY_KEYBOARD.row(InlineKeyboardButton(text='↪️ Вернуться в аккаунт',
                                              callback_data=f"get_account:{account_id}"))
    return HISTORY_KEYBOARD.as_markup()
