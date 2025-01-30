from .account_repo import *
from .card_repo import *
from .presents_repo import *
from .ride_repo import *
from .user_repo import *

user_repository = UserRepository()
account_repository = AccountsRepository()
cards_repository = CardsRepository()
rides_repository = RidesRepository()
presents_repository = PresentsRepository()

__all__ = ['user_repository', 'account_repository', 'cards_repository', 'rides_repository', 'presents_repository']

