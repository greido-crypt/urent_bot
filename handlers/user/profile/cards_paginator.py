from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import CallbackQuery, Message
from pydantic import BaseModel

from data import generate_cancel_kb
from db.repository import cards_repository, user_repository
from loader import UserStates
from utils import CardsPaginator, PaymentCardsPaginator
from utils.luhn_detector import validate_credit_card

cards_paginator_router = Router()


class Card(BaseModel):
    card_number: str = None
    card_month: str = None
    card_year: str = None
    card_cvc: str = None


@cards_paginator_router.callback_query(F.data.startswith(('remove_card')))
async def remove_card(call: CallbackQuery):
    _, card_id = call.data.split(':')
    await cards_repository.updateIsDeletedByCardId(card_id=int(card_id))
    await call.answer('Карта успешно удалена!', show_alert=True)
    await send_cards_list_menu(call)


@cards_paginator_router.callback_query(F.data.startswith(('add_card')))
async def add_card(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('<b>Пришлите номер карты в виде: <code>2200013244212123</code></b>',
                                 reply_markup=generate_cancel_kb())
    await state.update_data(cancel_message=call)
    await state.set_state(UserStates.input_card_number)


@cards_paginator_router.message(UserStates.input_card_number)
async def input_card_number(message: Message, state: FSMContext):
    card_number = ''.join(char for char in message.text if char.isdigit())
    if not validate_credit_card(card_number):
        return await message.reply('<b>❌ Введите правильно номер карты!</b>')
    state_data = await state.get_data()
    cancel_message: CallbackQuery = state_data['cancel_message']
    await cancel_message.message.edit_reply_markup()

    cancel_message: Message = await message.answer('<b>Пришлите дату карты (месяц/год): <code>12/30</code></b>',
                                                   reply_markup=generate_cancel_kb())
    card_model = Card()
    card_model.card_number = card_number
    await state.update_data(cancel_message=cancel_message, card_model=card_model)
    await state.set_state(UserStates.input_card_expiration)


@cards_paginator_router.message(UserStates.input_card_expiration)
async def input_card_expiration(message: Message, state: FSMContext):
    card_expiration = message.text.split('/')
    if len(card_expiration) != 2 and not card_expiration[1].isdigit() or not card_expiration[0].isdigit():
        return await message.reply('<b>Введите дату карты правильно!</b>')
    state_data = await state.get_data()
    cancel_message: Message = state_data['cancel_message']
    card_model: Card = state_data['card_model']
    card_model.card_month, card_model.card_year = card_expiration
    await cancel_message.edit_reply_markup()

    cancel_message: Message = await message.answer('<b>Пришлите cvc карты: <code>321</code></b>',
                                                   reply_markup=generate_cancel_kb())
    await state.update_data(cancel_message=cancel_message, card_model=card_model)
    await state.set_state(UserStates.input_card_cvc)


@cards_paginator_router.message(UserStates.input_card_cvc)
async def input_card_cvc(message: Message, state: FSMContext):
    card_cvc = message.text
    if len(card_cvc) != 3 and not card_cvc.isdigit():
        return await message.reply('<b>Введите cvc карты правильно!</b>')
    state_data = await state.get_data()
    await state.clear()
    cancel_message: Message = state_data['cancel_message']
    card_model: Card = state_data['card_model']
    await cancel_message.edit_reply_markup()
    card_model.card_cvc = card_cvc
    card_data = await cards_repository.getCardByNumber(number=card_model.card_number)
    if card_data:
        await cards_repository.updateCardDataById(card_id=card_data.id,
                                                  number=card_model.card_number,
                                                  cvc=card_model.card_cvc,
                                                  date=f'{card_model.card_month}/{card_model.card_year}',
                                                  user_id=message.from_user.id)
    else:
        await cards_repository.addCard(number=card_model.card_number,
                                       date=f'{card_model.card_month}/{card_model.card_year}',
                                       cvc=card_model.card_cvc,
                                       user_id=message.from_user.id)
    await message.answer('<b>Карта успешно добавлена в ваш список</b>')


@cards_paginator_router.callback_query(F.data.startswith(('cards_paginator')), any_state)
async def send_cards_list_menu(call: CallbackQuery):
    cards_list = await cards_repository.getCardsByUserId(user_id=call.from_user.id)
    try:
        _, method, page_now = call.data.split(':')
    except:
        method, page_now = 'send_menu', 1

    cards_paginator = CardsPaginator(items=cards_list, page_now=int(page_now))
    if method == 'page_next':
        return await call.message.edit_text(text=cards_paginator.__str__(),
                                            reply_markup=cards_paginator.generate_next_page())
    elif method == 'page_now':
        return await call.answer(f'Вы находитесь на странице: {page_now}', show_alert=True)
    elif method == 'page_prev':
        return await call.message.edit_text(text=cards_paginator.__str__(),
                                            reply_markup=cards_paginator.generate_prev_page())
    elif method == 'send_menu':
        return await call.message.edit_text(text=cards_paginator.__str__(),
                                            reply_markup=cards_paginator.generate_now_page())


@cards_paginator_router.callback_query(F.data.startswith(('payment_cards_paginator')), any_state)
async def payment_cards_paginator(call: CallbackQuery):
    cards_list = await cards_repository.getCardsByUserId(user_id=call.from_user.id)
    try:
        _, method, page_now = call.data.split(':')
    except:
        method, page_now = 'send_menu', 1

    payment_cards_paginator = PaymentCardsPaginator(items=cards_list, page_now=int(page_now))

    if method == 'page_next':
        return await call.message.edit_text(text=payment_cards_paginator.__str__(),
                                            reply_markup=payment_cards_paginator.generate_next_page())
    elif method == 'page_now':
        return await call.answer(f'Вы находитесь на странице: {page_now}', show_alert=True)

    elif method == 'page_prev':
        return await call.message.edit_text(text=payment_cards_paginator.__str__(),
                                            reply_markup=payment_cards_paginator.generate_prev_page())
    elif method == 'send_menu':
        return await call.message.edit_text(text=payment_cards_paginator.__str__(),
                                            reply_markup=payment_cards_paginator.generate_now_page())
