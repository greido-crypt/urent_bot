from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import CallbackQuery

from db.repository import account_repository
from utils import AccountPaginator

account_paginator_router = Router()


@account_paginator_router.callback_query(F.data.startswith(('account_paginator')), any_state)
async def send_accounts_list_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    accounts_list = await account_repository.getAccountsByUserId(user_id=call.from_user.id)
    _, method, page_now = call.data.split(':')
    account_paginator = AccountPaginator(items=accounts_list, page_now=int(page_now))
    if method == 'page_next':
        return await call.message.edit_text(text=account_paginator.__str__(),
                                            reply_markup=account_paginator.generate_next_page())
    elif method == 'page_now':
        return await call.answer(f'Вы находитесь на странице: {page_now}', show_alert=True)
    elif method == 'page_prev':
        return await call.message.edit_text(text=account_paginator.__str__(),
                                            reply_markup=account_paginator.generate_prev_page())
    elif method == 'send_menu':
        return await call.message.edit_text(text=account_paginator.__str__(),
                                            reply_markup=account_paginator.generate_now_page())

