import traceback
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.types import TelegramObject, CallbackQuery

from loader import bot_logger
from settings import CHANNEL_ID


class CallbackSpamMiddleware(BaseMiddleware):
    def __init__(self, debug: bool = False):
        self.storage: Dict[int, Dict[str, bool]] = {}
        self.debug = debug
        if self.debug:
            print("CallbackSpamMiddleware initialized with debugging enabled.")

    def log(self, message: str) -> None:
        """Helper method to print logs if debugging is enabled."""
        if self.debug:
            print(message)

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        callback_prefix = event.data.split(':')[0]

        # Log the incoming callback data
        self.log(f"Received callback: user_id={user_id}, callback_prefix={callback_prefix}")

        # Initialize the user's storage if it doesn't exist
        if user_id not in self.storage:
            self.storage[user_id] = {}
            self.log(f"Initialized storage for user_id={user_id}.")

        user_storage = self.storage[user_id]

        # Check if there's an active callback being processed for this user
        if any(user_storage.values()):
            self.log(
                f"User {user_id} already has an active callback, ignoring new callback with prefix {callback_prefix}.")
            return  # Ignore the event if there's any active callback for the user

        # If this callback prefix is already in the storage, ignore it
        if user_storage.get(callback_prefix, False):
            self.log(f"Callback with prefix {callback_prefix} for user_id={user_id} is already active, ignoring.")
            return

        # Mark the current callback prefix as active
        user_storage[callback_prefix] = True
        self.log(f"Callback with prefix {callback_prefix} for user_id={user_id} marked as active.")

        try:
            await handler(event, data)
        except TelegramBadRequest:
            return await self.__call__(handler, event, data)
        except TelegramNetworkError:
            return await self.__call__(handler, event, data)
        except Exception as e:
            self.log(f"Error while handling callback for user_id={user_id}, prefix={callback_prefix}: {e}")
            try:
                await bot_logger.send_message(chat_id=CHANNEL_ID,
                                              text=f'<b>🚫 Ошибка в CallBack: {traceback.format_exc()}</b>')
            except:
                pass
        finally:
            # After processing, mark the callback prefix as inactive
            user_storage[callback_prefix] = False
            self.log(f"Callback with prefix {callback_prefix} for user_id={user_id} marked as inactive.")

        self.log(f"Final storage state for user_id={user_id}: {self.storage[user_id]}")
        return
