import datetime
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from loguru import logger

from settings import BOTS_TOKENS, BOT_LOGGER


class UserStates(StatesGroup):
    input_promo_code = State()
    input_key = State()
    input_scooter = State()
    input_card_number = State()
    input_card_expiration = State()
    input_card_cvc = State()


class AdminStates(StatesGroup):
    input_account = State()
    input_user = State()
    input_card = State()


bots_list = [Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='html')) for BOT_TOKEN in BOTS_TOKENS]
bot_logger = Bot(token=BOT_LOGGER, default=DefaultBotProperties(parse_mode='html'))

commands = [BotCommand(command='start', description='Запустить бота'),
            BotCommand(command='help', description='Помощь')]

dp = Dispatcher(storage=MemoryStorage())

logger.add(f"logs/{datetime.date.today()}.log", format="{time:DD-MMM-YYYY HH:mm:ss} | {level:^25} | {message}",
           enqueue=True, rotation="00:00")

logger.level("JOIN", no=60, color="<green>")

logger.level("SPAM", no=60, color="<red>")
logger.level("TOKEN IS EXPIRED", no=60, color="<red>")
logger.level("LINK-CARD-DENY", no=60, color="<red>")
logger.level("DELETE-ACCOUNT", no=60, color="<red>")

logger.level("USE-KEY", no=60, color="<blue>")
logger.level("START-UR-RIDE", no=60, color="<blue>")
logger.level("END-UR-RIDE", no=60, color="<blue>")
logger.level("PAUSE-UR-RIDE", no=60, color="<blue>")
logger.level("RESUME-UR-RIDE", no=60, color="<blue>")
logger.level("GET-COST-UR-RIDE", no=60, color="<blue>")

logger.level("LINK-CARD", no=60, color="<yellow>")
logger.level("UNLINK-CARDS", no=60, color="<yellow>")
