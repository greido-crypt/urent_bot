import asyncio
import traceback
from operator import attrgetter
from pprint import pprint

import aiofiles

from api import UrentAPI
from db.models import Accounts
from db.repository import account_repository


async def recheck(account: Accounts):
    # Попытка инициализации UrentAPI
    try:
        urent_api = UrentAPI(refresh_token=account.refresh_token,
                             access_token=account.access_token,
                             add_UrRequestData=False,
                             debug=False)
    except Exception:
        # Запись купона в файл при ошибке токенов и обновление статуса аккаунта
        async with aiofiles.open('banned_coupons.txt', mode='a') as banned_file:
            await banned_file.write(f'{account.coupon}\n')
        return await account_repository.updateAccountStatusWrongRefreshTokenByPhoneNumber(phone_number=account.phone_number)

    try:
        # Получение платежного профиля
        payment_profile = await urent_api.get_payment_profile()

        if payment_profile.wrong_refresh_token:
            async with aiofiles.open('banned_coupons.txt', mode='a') as banned_file:
                await banned_file.write(f'{account.coupon}\n')
            return

        # Параллельное получение промоакций и карт
        promo_actions, cards_info, orders = await asyncio.gather(
            urent_api.get_promo_actions(),
            urent_api.get_cards(),
            urent_api.get_orders()
        )

        # Удаление всех привязанных карт
        cards_id = [card.id for card in cards_info.entries]
        await asyncio.gather(*(urent_api.remove_card(card_id=card_id) for card_id in cards_id))
        # Проверка промокодов и бонусов
        if not payment_profile.promoCodes and payment_profile.bonuses.value == 0 and not account.wrong_activation_promo:
            coupon = await account_repository.resetAccountByAccountId(account_id=account.id, change_coupon=True)

            if coupon:
                account = await account_repository.getAccountByAccountId(account_id=account.id)

            # Обновление функциональности аккаунта
            await account_repository.updateAccountFunctionalityByAccountId(account_id=account.id, account_functionality=0)

            # Запись в файл
            filename = f'0 {bool(account.ya_token)} {payment_profile.bonuses.value}.txt'
            async with aiofiles.open(filename, mode='a') as balance_file:
                await balance_file.write(f'{account.coupon}\n')

        elif payment_profile.bonuses.value > 0:

            # Сброс купона
            coupon = await account_repository.resetAccountByAccountId(account_id=account.id, change_coupon=True)
            if coupon:
                account = await account_repository.getAccountByAccountId(account_id=account.id)

            # Определение функциональности аккаунта
            functionality = 2 if promo_actions.entries or (
                not payment_profile.promoCodes and account.promo_code and not orders.entries and not account.wrong_activation_promo
            ) else 1

            await account_repository.updateAccountFunctionalityByAccountId(account_id=account.id, account_functionality=functionality)

            # Запись в файл
            filename = f'{functionality} {bool(account.ya_token)} {payment_profile.bonuses.value}.txt'
            async with aiofiles.open(filename, mode='a') as balance_file:
                await balance_file.write(f'{account.coupon}\n')

    except Exception:
        # Логирование ошибки и запись купона в файл ошибок
        print(traceback.format_exc())
        async with aiofiles.open('errors_coupons.txt', mode='a') as error_file:
            await error_file.write(f'{account.coupon}\n')
        return



async def preparation_recheck_from_coupons():
    with open('coupons.txt', 'r') as f:
        couponsList = f.read().splitlines()
        coupons = {}
        for coupon in couponsList:
            coupons[coupon] = True

    all_accounts = await account_repository.getAllAccounts()
    accounts = [account for account in all_accounts if coupons.get(account.coupon, False)]
    batch_size = 65

    for i in range(0, len(accounts), batch_size):
        batch = accounts[i:i + batch_size]
        await asyncio.gather(*(recheck(account) for account in batch))


async def preparation_recheck():
    accounts = await account_repository.getAllAccountsByAccountFunctionality(account_functionality=2)
    accounts += await account_repository.getAllAccountsByAccountFunctionality(account_functionality=0)
    accounts += await account_repository.getAllAccountsByAccountFunctionality(account_functionality=1)
    # accounts = [account for account in accounts]
    #
    # accounts = sorted(accounts, key=attrgetter('creation_date'))

    batch_size = 85

    for i in range(0, len(accounts), batch_size):
        batch = accounts[i:i + batch_size]
        await asyncio.gather(*(recheck(account) for account in batch))


asyncio.run(preparation_recheck_from_coupons())
