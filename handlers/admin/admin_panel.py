from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from api import UrentAPI
from data import generate_account_kb, generate_get_account_kb_by_id
from data.keyboards import generate_admin_menu_kb, generate_go_to_support_kb, generate_back_to_account_kb
from db.repository import account_repository, rides_repository
from handlers.user.account import get_account_data
from loader import AdminStates
from settings import ADMIN_LIST

admin_router = Router(name="admin_router")


@admin_router.message(Command('admin'))
async def admin(message: Message):
    await message.answer('<b>⚡️ Вы вошли в меню администратора:</b>',
                         reply_markup=generate_admin_menu_kb())


@admin_router.callback_query(F.data.startswith(('card_management', 'user_management', 'account_management')))
async def admin_management(call: CallbackQuery, state: FSMContext):
    if call.data == 'user_management':
        await call.message.edit_text('<b>Пришлите мне telegram id:</b>')
        await state.set_state(AdminStates.input_user)
    elif call.data == 'account_management':
        await call.message.edit_text('<b>Пришлите мне ключ аккаунта:</b>')
        await state.set_state(AdminStates.input_account)
    elif call.data == 'card_management':
        await call.message.edit_text('<b>Пришлите мне номер карты:</b>')
        await state.set_state(AdminStates.input_card)

    await state.update_data(call=call)


@admin_router.message(AdminStates.input_account)
async def input_account(message: Message, state: FSMContext):
    return await get_account_data(event=message, state=state)




@admin_router.callback_query(F.data.startswith(('recover_account', 'reset_activation')))
async def admin_manipulation_account(call: CallbackQuery):
    method: str
    account_id: str
    method, account_id = call.data.split(':')
    account_data = await account_repository.getAccountByAccountId(account_id=int(account_id))
    if method == 'recover_account':
        await account_repository.updateAccountIsDeletedStatusByAccountId(account_id=account_data.id, is_deleted=False)
        await call.message.edit_text(text='<b>✅ Аккаунт восстановлен</b>',
                                     reply_markup=generate_back_to_account_kb(account_id=account_data.id))
    elif method == 'reset_activation':
        await account_repository.resetAccountByAccountId(account_id=account_data.id)
        await call.message.edit_text(text='<b>✅ Аккаунт сброшен</b>',
                                     reply_markup=generate_back_to_account_kb(account_id=account_data.id))


@admin_router.message(AdminStates.input_card)
async def input_card(message: Message, state: FSMContext):
    await state.clear()

    ...


@admin_router.message(AdminStates.input_user)
async def input_user(message: Message, state: FSMContext):
    await state.clear()

    ...
