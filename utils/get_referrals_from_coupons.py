import asyncio
from operator import attrgetter

import aiofiles

from api import UrentAPI
from db.models import Accounts
from db.repository import account_repository


async def get_referral(account: Accounts):
    try:
        urent_api = UrentAPI(refresh_token=account.refresh_token,
                             access_token=account.access_token,
                             add_UrRequestData=False,
                             debug=True)
    except:
        async with aiofiles.open(f'banned_coupons.txt', mode='a') as banned_file:
            await banned_file.write(f'{account.coupon}\n')

        return await account_repository.updateAccountStatusWrongRefreshTokenByPhoneNumber(
            phone_number=account.phone_number)

    try:
        response = await urent_api.get_referral_info()
    except:
        return

    if response.wrong_refresh_token:
        return

    async with aiofiles.open('referrals.txt', mode='a') as referrals_file:
        await referrals_file.write(f'{response.referralCode}\n')


async def preparation_get_referrals_from_coupons():
    with open('coupons.txt', 'r') as f:
        coupons = f.read().splitlines()
    all_accounts = await account_repository.getAllAccounts()
    accounts = [account for account in all_accounts if account.coupon in coupons]
    batch_size = 50

    for i in range(0, len(accounts), batch_size):
        batch = accounts[i:i + batch_size]
        await asyncio.gather(*(get_referral(account) for account in batch))


async def preparation_get_referrals():
    all_accounts = await account_repository.getAllAccountsByAccountFunctionality(account_functionality=1)
    all_accounts = [account for account in all_accounts if account.ya_token]
    coupons = sorted(all_accounts, key=attrgetter('creation_date'), reverse=True)[:500]
    batch_size = 50
    for i in range(0, len(coupons), batch_size):
        batch = coupons[i:i + batch_size]
        await asyncio.gather(*(get_referral(account) for account in batch))


asyncio.run(preparation_get_referrals())
