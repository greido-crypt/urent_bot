import datetime
import aiofiles
import asyncio

from db.repository import account_repository


async def main():
    # Получаем все аккаунты с определенной функциональностью
    accounts = await account_repository.getAllAccountsByAccountFunctionality(account_functionality=0)

    # Фильтруем аккаунты, у которых разница с текущей датой <= 1 день
    one_day_delta = datetime.timedelta(days=1)
    accounts = [account for account in accounts if (datetime.datetime.utcnow() - account.upd_date) <= one_day_delta]

    # Записываем подходящие купоны в файл
    async with aiofiles.open('coupons.txt', mode='a') as error_file:
        for account in accounts:
            await error_file.write(f'{account.coupon}\n')


# Запускаем асинхронную функцию
asyncio.run(main())
