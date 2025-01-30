import datetime
import math
from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models import Accounts, Cards


class Paginator:
    def __init__(self,
                 items: List,
                 name_of_paginator: str = None,
                 page_now=0,
                 per_page=10):
        self.items = items
        self.per_page = per_page
        self.page_now = page_now
        self.name_paginator = name_of_paginator

    def _generate_page(self):
        ...

    def __str__(self):
        ...


class HistoryPaginator(Paginator):
    def __init__(self, items: List, page_now=1, per_page=4):
        super().__init__(items=items,
                         page_now=page_now,
                         per_page=per_page,
                         name_of_paginator='history_paginator')

    def _generate_page(self) -> InlineKeyboardMarkup:
        self.items: List[Accounts] = self.items
        page_kb = InlineKeyboardBuilder()

        if self.page_now <= 0:
            self.page_now = 1

        if not bool(len(self.items[(self.page_now - 1) * self.per_page:self.page_now * self.per_page])):
            self.page_now = 1

        for key_data in self.items[(self.page_now - 1) * self.per_page:self.page_now * self.per_page]:
            page_kb.row(InlineKeyboardButton(text=f'🔍 {key_data.coupon}',
                                             callback_data=f'{self.name_paginator}:look:{key_data.id}'))
        page_kb.row(InlineKeyboardButton(text='◀️ Назад',
                                         callback_data=f'{self.name_paginator}:page_prev:{self.page_now}'))
        page_kb.add(InlineKeyboardButton(text=f'{self.page_now}/{math.ceil(self.items.__len__() / self.per_page)}',
                                         callback_data=f'{self.name_paginator}:page_now:{self.page_now}'))
        page_kb.add(InlineKeyboardButton(text='Вперед ▶️',
                                         callback_data=f'{self.name_paginator}:page_next:{self.page_now}'))
        page_kb.row(InlineKeyboardButton(text='🔽 Вернуться в личный кабинет',
                                         callback_data='back_to_personal_area'))
        return page_kb.as_markup()

    def generate_next_page(self) -> InlineKeyboardMarkup:
        self.page_now += 1
        return self._generate_page()

    def generate_prev_page(self) -> InlineKeyboardMarkup:
        self.page_now -= 1
        return self._generate_page()

    def generate_now_page(self) -> InlineKeyboardMarkup:
        return self._generate_page()

    def __str__(self):
        return '<b>🟣 Список ваших активаций:</b>'


class AccountPaginator(Paginator):
    def __init__(self, items: List, page_now=1, per_page=4):
        super().__init__(items=items,
                         page_now=page_now,
                         per_page=per_page,
                         name_of_paginator='account_paginator')

    def _generate_page(self) -> InlineKeyboardMarkup:
        self.items: List[Accounts] = self.items
        page_kb = InlineKeyboardBuilder()

        if self.page_now <= 0:
            self.page_now = 1

        if not bool(len(self.items[(self.page_now - 1) * self.per_page:self.page_now * self.per_page])):
            self.page_now = 1

        for key_data in self.items[(self.page_now - 1) * self.per_page:self.page_now * self.per_page]:
            if key_data.account_functionality == 0 and key_data.ya_token:
                button_text = f'🏷️ + 🔥 {key_data.phone_number}'
            elif key_data.account_functionality == 0:
                button_text = f'🏷️ {key_data.phone_number}'
            elif key_data.account_functionality == 1 and key_data.ya_token:
                button_text = f'⭐ + 🔥 {key_data.phone_number}'
            elif key_data.account_functionality == 1:
                button_text = f'⭐ {key_data.phone_number}'
            elif key_data.account_functionality == 2 and key_data.ya_token:
                button_text = f'🏷️ + ⭐ + 🔥 {key_data.phone_number}'
            else:
                button_text = f'{key_data.phone_number}'

            page_kb.row(InlineKeyboardButton(text=button_text,
                                             callback_data=f'get_account:{key_data.id}'))

        page_kb.row(InlineKeyboardButton(text='◀️ Назад',
                                         callback_data=f'{self.name_paginator}:page_prev:{self.page_now}'))
        page_kb.add(InlineKeyboardButton(text=f'{self.page_now}/{math.ceil(self.items.__len__() / self.per_page)}',
                                         callback_data=f'{self.name_paginator}:page_now:{self.page_now}'))
        page_kb.add(InlineKeyboardButton(text='Вперед ▶️',
                                         callback_data=f'{self.name_paginator}:page_next:{self.page_now}'))
        page_kb.row(InlineKeyboardButton(text='↪️ Вернуться в личный кабинет',
                                         callback_data='back_to_personal_area'))
        return page_kb.as_markup()

    def generate_next_page(self) -> InlineKeyboardMarkup:
        self.page_now += 1
        return self._generate_page()

    def generate_prev_page(self) -> InlineKeyboardMarkup:
        self.page_now -= 1
        return self._generate_page()

    def generate_now_page(self) -> InlineKeyboardMarkup:
        return self._generate_page()

    def __str__(self):
        return '<b>🟣 Список ваших аккаунтов:</b>'


class CardsPaginator(Paginator):
    def __init__(self, items: List[Cards], page_now=1, per_page=4):
        super().__init__(items=items,
                         page_now=page_now,
                         per_page=per_page,
                         name_of_paginator='cards_paginator')

    def _generate_page(self) -> InlineKeyboardMarkup:
        self.items: List[Cards] = self.items
        page_kb = InlineKeyboardBuilder()

        if self.page_now <= 0:
            self.page_now = 1

        if not bool(len(self.items[(self.page_now - 1) * self.per_page:self.page_now * self.per_page])):
            self.page_now = 1

        for card_data in self.items[(self.page_now - 1) * self.per_page:self.page_now * self.per_page]:
            if card_data.ecom_pay + card_data.yoomoney + card_data.mts_pay <= 6:
                page_kb.row(InlineKeyboardButton(text=f'🟢 {card_data.number}',
                                                 callback_data=f'get_card:{card_data.id}'))

            elif card_data.ecom_pay + card_data.yoomoney + card_data.mts_pay < 12:
                page_kb.row(
                    InlineKeyboardButton(text=f'🟠 {card_data.number}', callback_data=f'get_card:{card_data.id}'))

            elif card_data.ecom_pay + card_data.yoomoney + card_data.mts_pay == 16:
                page_kb.row(InlineKeyboardButton(text=f'🔴 {card_data.number}',
                                                 callback_data=f'get_card:{card_data.id}'))

            page_kb.add(InlineKeyboardButton(text='❌ Удалить карту',
                                             callback_data=f'remove_card:{card_data.id}'))
        page_kb.row(InlineKeyboardButton(text='✏️ Добавить карту',
                                         callback_data='add_card'))
        page_kb.row(InlineKeyboardButton(text='◀️ Назад',
                                         callback_data=f'{self.name_paginator}:page_prev:{self.page_now}'))
        page_kb.add(InlineKeyboardButton(text=f'{self.page_now}/{math.ceil(self.items.__len__() / self.per_page)}',
                                         callback_data=f'{self.name_paginator}:page_now:{self.page_now}'))
        page_kb.add(InlineKeyboardButton(text='Вперед ▶️',
                                         callback_data=f'{self.name_paginator}:page_next:{self.page_now}'))
        page_kb.row(InlineKeyboardButton(text='↪️ Вернуться в личный кабинет',
                                         callback_data='back_to_personal_area'))
        return page_kb.as_markup()

    def generate_next_page(self) -> InlineKeyboardMarkup:
        self.page_now += 1
        return self._generate_page()

    def generate_prev_page(self) -> InlineKeyboardMarkup:
        self.page_now -= 1
        return self._generate_page()

    def generate_now_page(self) -> InlineKeyboardMarkup:
        return self._generate_page()

    def __str__(self):
        return '<b>🟣 Список ваших карт:</b>'


class PaymentCardsPaginator(CardsPaginator):
    def __init__(self, items: List[Cards], account_id: int | str, page_now=1, per_page=8):
        self.__account_id = account_id
        self.name_paginator = 'payment_cards_paginator'
        super().__init__(items, page_now=page_now, per_page=per_page)

    def _generate_page(self) -> InlineKeyboardMarkup:
        keys: List[Cards] = self.items
        page_kb = InlineKeyboardBuilder()

        if self.page_now <= 0:
            self.page_now = 1

        if not bool(len(keys[(self.page_now - 1) * self.per_page:self.page_now * self.per_page])):
            self.page_now = 1

        for card_data in keys[(self.page_now - 1) * self.per_page:self.page_now * self.per_page]:
            if card_data.ecom_pay + card_data.yoomoney + card_data.mts_pay <= 6:
                page_kb.row(InlineKeyboardButton(text=f'🟢 {card_data.number}',
                                                 callback_data=f'pay_card:{self.__account_id}:{card_data.id}'))

            elif card_data.ecom_pay + card_data.yoomoney + card_data.mts_pay < 12:
                page_kb.row(InlineKeyboardButton(text=f'🟠 {card_data.number}',
                                                 callback_data=f'pay_card:{self.__account_id}:{card_data.id}'))

            elif card_data.ecom_pay + card_data.yoomoney + card_data.mts_pay == 12:
                page_kb.row(InlineKeyboardButton(text=f'🔴 {card_data.number}',
                                                 callback_data=f'pay_card:{self.__account_id}:{card_data.id}'))

        page_kb.row(InlineKeyboardButton(text='🔥 Mir Pay 🔥', callback_data=f'pay_card_mir:{self.__account_id}'))
        page_kb.row(InlineKeyboardButton(text='🔥 Sber Pay 🔥', callback_data=f'pay_card_sb:{self.__account_id}'))
        page_kb.row(InlineKeyboardButton(text='🔥 Tinkoff Pay 🔥', callback_data=f'pay_card_tinkoff:{self.__account_id}'))
        page_kb.row(InlineKeyboardButton(text='✏️ Добавить карту', callback_data='add_card'))

        page_kb.row(
            InlineKeyboardButton(text='◀️ Назад', callback_data=f'{self.name_paginator}:page_prev:{self.page_now}'))
        page_kb.add(InlineKeyboardButton(text=f'{self.page_now}/{math.ceil(keys.__len__() / self.per_page)}',
                                         callback_data=f'{self.name_paginator}:page_now:{self.page_now}'))
        page_kb.add(
            InlineKeyboardButton(text='Вперед ▶️', callback_data=f'{self.name_paginator}:page_next:{self.page_now}'))
        page_kb.row(InlineKeyboardButton(text='↪️ Вернуться', callback_data=f"get_account:{self.__account_id}"))

        return page_kb.as_markup()

    def generate_next_page(self) -> InlineKeyboardMarkup:
        self.page_now += 1
        return self._generate_page()

    def generate_prev_page(self) -> InlineKeyboardMarkup:
        self.page_now -= 1
        return self._generate_page()

    def generate_now_page(self) -> InlineKeyboardMarkup:
        return self._generate_page()

    def __str__(self):
        return ('<b>🟣 Доступные способы привязки:</b>')
