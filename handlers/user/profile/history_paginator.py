from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import CallbackQuery

from db.repository import account_repository
from utils import HistoryPaginator

history_paginator_router = Router()


@history_paginator_router.callback_query(F.data.contains(('look')), any_state)
async def look_callback_query(call: CallbackQuery):
    """
        paginator, method, page_now or __account_id
        """
    _, method, account_id = call.data.split(":")
    acc_data = await account_repository.getAccountByAccountId(account_id=int(account_id))
    return await call.answer(f'Дата создания ключа: {acc_data.creation_date.strftime("%d/%m/%Y")}')


@history_paginator_router.callback_query(F.data.startswith(('history_paginator')), any_state)
async def send_history_menu(call: CallbackQuery):
    tg_user_id = call.from_user.id
    accounts_deleted = await account_repository.getAccountsByUserId(user_id=tg_user_id, is_deleted=True)
    accounts_not_deleted = await account_repository.getAccountsByUserId(user_id=tg_user_id)
    list_of_purchases = accounts_deleted + accounts_not_deleted
    """
    paginator, method, page_now or item_id
    """
    _, method, page_now = call.data.split(":")
    history_paginator = HistoryPaginator(items=list_of_purchases, page_now=int(page_now))
    if not bool(len(list_of_purchases)):
        return await call.answer('Список активаций пуст :(\n'
                                 'Давай исправим это ?', show_alert=True)
    elif method == 'page_next':
        return await call.message.edit_text(text=history_paginator.__str__(),
                                            reply_markup=history_paginator.generate_next_page())
    elif method == 'page_now':
        return await call.answer(f'Вы находитесь на странице: {page_now}', show_alert=True)
    elif method == 'page_prev':
        return await call.message.edit_text(text=history_paginator.__str__(),
                                            reply_markup=history_paginator.generate_prev_page())
    elif method == 'send_menu':
        return await call.message.edit_text(text=history_paginator.__str__(),
                                            reply_markup=history_paginator.generate_now_page())
