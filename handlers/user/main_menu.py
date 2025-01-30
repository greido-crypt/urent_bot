import datetime
import random
from operator import attrgetter

from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import CallbackQuery, Message
from loguru import logger

from data import generate_personal_area_kb, generate_get_account_kb_by_id, generate_main_menu_kb, \
    generate_cancel_kb, generate_help_kb
from data.keyboards import generate_inline_main_menu
from db.models import Presents
from settings import STICKER_ID,  CHANNEL_ID
from db.repository import account_repository, presents_repository
from db.repository import user_repository
from loader import UserStates

keyboard_router = Router(name='keyboard_router')


@keyboard_router.message(Command('start'), any_state)
async def get_text_messages(message: Message, state: FSMContext):
    await state.clear()
    await message.answer_sticker(random.choice(STICKER_ID))
    await message.answer(
        f"<b>Приветствую!\n"
        f"🛴💨 Рады видеть тебя снова в нашем сервисе! 🎉\n"
        "Готов ли ты отправиться в захватывающее путешествие на самокате с нами сегодня? 🌟✨</b>",
        reply_markup=generate_inline_main_menu())
    await message.answer('<b>Главное меню:</b>', reply_markup=generate_main_menu_kb())


@keyboard_router.message(F.text == '🔑 Ввести ключик')
async def enter_key(message: Message, state: FSMContext):
    cancel_message = await message.reply(
        f"<b>⚠️ Пожалуйста, обратите внимание, что при активации нового ключа существует вероятность потери баллов на предыдущем аккаунте.\n"
        f"❗ Активируя новый аккаунт, вы подтверждаете, что использовали все баллы на предыдущем аккаунте.\n\n"
        f"Если <u>Вы уверены в своих действиях</u> - Напишите мне, пожалуйста, ключ, который Вы приобрели в боте 😘</b>",
        reply_markup=generate_cancel_kb())
    await state.update_data(cancel_message=cancel_message)
    await state.set_state(UserStates.input_key)


@keyboard_router.message(F.text == '💬 Помощь')
@keyboard_router.message(Command('help'))
async def help_answer(message: Message):
    await message.answer(text='<b>💜 Меню помощи:</b>', reply_markup=generate_help_kb())


@keyboard_router.message(UserStates.input_key)
async def input_key(message: Message, state: FSMContext, bot: Bot):
    cancel_message: Message = (await state.get_data())['cancel_message']
    await state.clear()
    coupon = message.text
    tg_user_id = message.from_user.id
    account_data = await account_repository.getAccountByCoupon(coupon=coupon)
    if account_data and account_data.user_id is None:
        await account_repository.updateAccountUserId(account_data.id, user_id=tg_user_id)
        await message.answer('<b>✅ Ключ подошёл 😉\n'
                             '📝 Аккаунт успешно загружен в личный кабинет!</b>',
                             reply_markup=generate_get_account_kb_by_id(account_data.id))
        await cancel_message.edit_reply_markup()
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"<b>💜 Пользователь: @{message.from_user.username}\n"
                 f"✅ Активировал ключ <code>{coupon}</code></b>")
    else:
        await message.answer(f"<b>❌ Ключ не подходит 😥</b>")


@keyboard_router.callback_query(F.data == 'back_to_personal_area')
@keyboard_router.message(F.text == 'ℹ️ Личный кабинет')
async def personal_area(event: CallbackQuery | Message):
    tg_user_id = event.from_user.id
    accounts_deleted = await account_repository.getAccountsByUserId(user_id=tg_user_id, is_deleted=True)
    accounts_not_deleted = await account_repository.getAccountsByUserId(user_id=tg_user_id)
    number_of_purchases = len(accounts_deleted) + len(accounts_not_deleted)
    user_data = await user_repository.get_user_by_tg_id(user_id=tg_user_id)
    registration_date = user_data.creation_date.strftime('%Y-%m-%d %H:%M:%S')
    message_text = f'<b>💜 Пользователь: @{event.from_user.username}\n' \
                   f'🔑 Ваш Id: <code>{tg_user_id}</code>\n' \
                   f'💸 Количество покупок: {number_of_purchases}\n' \
                   f'📋 Дата регистрации: {registration_date}</b>'

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(message_text, reply_markup=generate_personal_area_kb())
    else:
        await event.answer(message_text, reply_markup=generate_personal_area_kb())


@keyboard_router.message(F.text == '🎁 Получить подарок', any_state)
async def getPresent(message: Message):
    presents = await presents_repository.getPresentsByUserId(user_id=message.from_user.id)
    if presents:
        presents = sorted(presents, key=attrgetter('upd_date'), reverse=True)
        print(presents[0].upd_date.day, datetime.datetime.day, presents[0].upd_date.day == datetime.datetime.day)
        if presents[0].upd_date.day == datetime.datetime.day:
            return await message.answer('<b>Приходите за подарком на следующий день ✨</b>')

    presents = await presents_repository.getPresents(is_active=False)
    if not presents:
        return await message.answer('<b>Подарки закончились, приходите за ними чуть позже 😢</b>')

    present: Presents = random.choice(presents)

    await account_repository.updateAccountUserId(account_id=present.account_id, user_id=message.from_user.id)
    await presents_repository.updatePresentUserIdByPresentId(present_id=present.id, user_id=message.from_user.id)
    await message.answer('<b>📝 Аккаунт успешно загружен в личный кабинет!</b>',
                         reply_markup=generate_get_account_kb_by_id(present.account_id))


@keyboard_router.callback_query(F.data == 'cancel')
async def cancel_callback_query(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(text='<b>Действие успешно отменено</b>')


@keyboard_router.message()
async def any_messages(message: Message):
    await message.reply(f"Я вас не понимаю 😥\n"
                        f"Напишите <b>/start</b> или <b>/help</b>", reply_markup=generate_main_menu_kb())

