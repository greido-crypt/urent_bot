# -*- coding: utf-8 -*-
import asyncio

from data import generate_back_to_account_kb
from db.models import Accounts, Rides
from loader import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from colorama import Style, Fore
from api import UrentAPI
from db.repository import account_repository, rides_repository, user_repository, cards_repository
from handlers import register_user_commands
from settings import CARD_BAN_TIME, CHANNEL_ID
from utils.callback_throttling import CallbackSpamMiddleware
from utils.message_throttling import MessageSpamMiddleware


async def on_startup(dp):
    register_user_commands(dp)
    for bot in bots_list:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_my_commands(commands)
        bot_info = await bot.get_me()
        print(f"{Style.BRIGHT}{Fore.CYAN}https://t.me/{bot_info.username} запущен успешно!", Style.RESET_ALL)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(func=preparation_check_rides, trigger="interval", seconds=30)
    # scheduler.add_job(func=preparation_remove_cards, trigger="cron", hour=6)
    scheduler.add_job(func=updates_cards_info, trigger="interval", minutes=30)
    scheduler.start()


async def updates_cards_info():
    cards = await cards_repository.get_all_cards()
    for card in cards:
        if card.upd_date and card.upd_date + datetime.timedelta(days=CARD_BAN_TIME) <= datetime.datetime.utcnow():
            await cards_repository.clearPaymentsSystems(card_id=card.id)


async def preparation_remove_cards():
    users = await user_repository.select_all_users()
    all_tasks = []
    for user in users:
        accounts = await account_repository.getAccountsByUserId(user.user_id)
        for account in accounts:
            all_tasks.append(asyncio.create_task(remove_cards(account)))
    await asyncio.gather(*all_tasks)


async def remove_cards(account: Accounts):
    urent_api = UrentAPI(access_token=account.access_token,
                         refresh_token=account.refresh_token)

    activity_info = await urent_api.get_activity()

    if activity_info.wrong_refresh_token:
        return

    cards_info = await urent_api.get_cards()

    if not cards_info.entries:
        return

    elif not activity_info.activities:
        cards_id = [data_card.id for data_card in cards_info.entries]
        for card_id in cards_id:
            await urent_api.remove_card(card_id=card_id)

        logger.log("UNLINK-CARDS", f'{account.user_id} | {account.phone_number}')
        return

    for bot in bots_list:
        try:
            await bot.send_message(chat_id=account.user_id,
                                   text=f'<b>Не удалось отвязать автоматически карту от аккаунта <code>{account.phone_number}</code>!\n'
                                        f'Как сможете отвязать карту - <u>отвяжите</u>, чтобы не возникло непредвиденных ситуаций с вашими средствами!</b>')
        finally:
            pass


async def preparation_check_rides():
    all_tasks = []
    rides = await rides_repository.get_all_rides_not_finished()
    for ride in rides:
        all_tasks.append(asyncio.create_task(check_ride(ride)))
    await asyncio.gather(*all_tasks)


async def check_ride(ride: Rides):
    for bot in bots_list:
        if ride.bot_id == bot.id:
            break
    else:
        return

    if ride.account.is_deleted:
        return await rides_repository.update_upd_date(ride_id=ride.id)

    if ride.finished_time > datetime.datetime.utcnow():
        return

    urent_api = UrentAPI(access_token=ride.account.access_token,
                         refresh_token=ride.account.refresh_token)

    activity_info = await urent_api.get_activity()
    if not activity_info.activities:
        return await rides_repository.update_upd_date(ride_id=ride.id)

    rate_id = activity_info.activities[0].rateId
    if not rate_id:
        return

    if rate_id != ride.rate_id:
        return await rides_repository.update_upd_date(ride_id=ride.id)

    response = await urent_api.stop_drive(activity_info=activity_info)
    await asyncio.sleep(2)

    activity_info = await urent_api.get_activity()

    if response.errors and activity_info.activities:
        error = response.errors[0].value[0]
        await bot_logger.send_message(chat_id=CHANNEL_ID,
                                      text=f'<b>🚫 Ошибка при при автоматическом завершении самоката: {error}\n'
                                           f"📞 Номер телефона: <code>{ride.account.phone_number}</code>\n"
                                           f"🎫 Купон: <code>{ride.account.coupon}</code>\n"
                                           f"💜 Пользователь: @{ride.account.user.username}</b>")

        return await bot.send_message(chat_id=ride.account.user_id,
                                      text=f'<b>🚫 Ошибка при при автоматическом завершении самоката: {error}\n'
                                           f"📞 Номер телефона: <code>{ride.account.phone_number}</code></b>",
                                      reply_markup=generate_back_to_account_kb(account_id=ride.account.id))

    await rides_repository.update_upd_date(ride_id=ride.id)

    await bot.send_message(chat_id=CHANNEL_ID,
                           text=f'<b>   ✅ Поездка была автоматически завершена:\n'
                                f"📞 Номер телефона: <code>{ride.account.phone_number}</code>\n"
                                f"🎫 Купон: <code>{ride.account.coupon}</code>\n"
                                f"💜 Пользователь: @{ride.account.user.username}</b>")

    await bot.send_message(chat_id=ride.account.user_id,
                           text='<b>✅ Поездка была автоматически завершена!\n'
                                f'📞 Номер телефона: <code>{ride.account.phone_number}</code>\n'
                                f'Рекомендуем отвязать карту после того, как совершили поездки на аккаунте во имя избежание списаний (штрафов и тд)</b>',
                           reply_markup=generate_back_to_account_kb(account_id=ride.account.id))


async def main() -> None:
    await on_startup(dp)
    # from db.engine import DatabaseEngine
    # db_engine = DatabaseEngine()
    # await db_engine.proceed_schemas()
    dp.message.middleware.register(MessageSpamMiddleware())
    dp.callback_query.middleware.register(CallbackSpamMiddleware())
    await dp.start_polling(*bots_list)


if __name__ == '__main__':
    asyncio.run(main())
