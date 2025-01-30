import secrets
import string
from typing import List, Sequence

from sqlalchemy import select, update

from db.engine import DatabaseEngine
from db.models import Accounts


class AccountsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_code(
            self,
            access_token: str,
            refresh_token: str,
            coupon: str,
            promo_code: str,
            phone_number: str,
            ya_token: str = None,
            account_functionality: int = None,
            fake_points: int = 0,
            fake_free_rides: int = 0,
            user_id: int = None):
        async with self.session_maker() as session:
            async with session.begin():
                keys = Accounts(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    coupon=coupon,
                    fake_points=fake_points,
                    phone_number=phone_number,
                    user_id=user_id,
                    promo_code=promo_code,
                    ya_token=ya_token,
                    fake_free_rides=fake_free_rides,
                    account_functionality=account_functionality
                )
                try:
                    session.add(keys)
                except Exception:
                    return False
                return True

    async def getAccountByCoupon(self, coupon: str) -> Accounts | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Accounts).where(Accounts.coupon == coupon)
                sql_res = await session.execute(sql)
                return sql_res.scalars().one_or_none()

    async def getAccountsByUserId(self,
                                  user_id: int,
                                  is_deleted: bool = False,
                                  wrong_refresh_token: bool = False) -> list[Accounts] | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Accounts).where(Accounts.user_id == user_id,
                                             Accounts.is_deleted == is_deleted,
                                             Accounts.wrong_refresh_token == wrong_refresh_token)
                sql_res = await session.execute(sql)
                return sql_res.scalars().all()

    async def getAccountByAccountId(self, account_id: int) -> Accounts | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Accounts).where(Accounts.id == account_id)
                sql_res = await session.execute(sql)
                return sql_res.scalars().one_or_none()

    async def updateAccessAndRefreshTokenByPhoneNumber(self, phone_number: str, access_token: str, refresh_token: str):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Accounts).values(
                    {
                        Accounts.refresh_token: refresh_token,
                        Accounts.access_token: access_token
                    }
                ).where(Accounts.phone_number == phone_number)
                await session.execute(sql)
                await session.commit()

    async def updateAccountUserId(self, account_id: int, user_id: int = None):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Accounts).values(
                    {
                        Accounts.user_id: user_id
                    }
                ).where(Accounts.id == account_id)
                await session.execute(sql)
                await session.commit()

    async def updateAccountIsDeletedStatusByAccountId(self, account_id: int, is_deleted: bool = True):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Accounts).values(
                    {
                        Accounts.is_deleted: is_deleted
                    }
                ).where(Accounts.id == account_id)
                await session.execute(sql)
                await session.commit()

    async def updateAccountIsDeletedStatusByNumber(self, phone_number: str, is_deleted: bool = True):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Accounts).values(
                    {
                        Accounts.is_deleted: is_deleted
                    }
                ).where(Accounts.phone_number == phone_number)
                await session.execute(sql)
                await session.commit()

    async def updateAccountStatusWrongActivationPromoByAccountId(self, account_id: int, wrong_activation_promo: bool = True):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Accounts).values(
                    {
                        Accounts.wrong_activation_promo: wrong_activation_promo
                    }
                ).where(Accounts.id == account_id)
                await session.execute(sql)
                await session.commit()


    async def updateAccountIsCardLinkedByAccountId(self, account_id: int, is_card_linked: bool = True):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Accounts).values(
                    {
                        Accounts.is_card_linked: is_card_linked
                    }
                ).where(Accounts.id == account_id)
                await session.execute(sql)
                await session.commit()

    async def updateAccountIsPromoCodeActivatedByAccountId(self, account_id: int, is_promo_code_activated: bool = True):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Accounts).values(
                    {
                        Accounts.is_promo_code_activated: is_promo_code_activated
                    }
                ).where(Accounts.id == account_id)
                await session.execute(sql)
                await session.commit()



    async def updateAccountStatusWrongRefreshTokenByAccountId(self, account_id: int, wrong_refresh_token: bool = True):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Accounts).values(
                    {
                        Accounts.wrong_refresh_token: wrong_refresh_token
                    }
                ).where(Accounts.id == account_id)
                await session.execute(sql)
                await session.commit()

    async def updateAccountStatusWrongRefreshTokenByPhoneNumber(self, phone_number: str, wrong_refresh_token: bool = True):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Accounts).values(
                    {
                        Accounts.wrong_refresh_token: wrong_refresh_token
                    }
                ).where(Accounts.phone_number == phone_number)
                await session.execute(sql)
                await session.commit()

    async def updateAccountFakePointsByAccountId(self, account_id: int, points: int | float):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Accounts).values(
                    {
                        Accounts.fake_points: points
                    }
                ).where(Accounts.id == account_id)
                await session.execute(sql)
                await session.commit()

    async def getAllAccounts(self) -> list[Accounts]:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Accounts)
                sql_res = await session.execute(sql)
                return sql_res.scalars().all()

    async def getAllAccountsByAccountFunctionality(self, account_functionality: int) -> Sequence[Accounts]:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Accounts).where(Accounts.account_functionality == account_functionality)
                sql_res = await session.execute(sql)
                return sql_res.scalars().all()

    async def resetAccountByAccountId(self, account_id: int, change_coupon: bool = False):
        async with (self.session_maker() as session):
            async with session.begin():
                coupon = None
                if not change_coupon:
                    sql = update(Accounts).values({
                        Accounts.user_id: None,
                        Accounts.is_deleted: False,
                        Accounts.wrong_activation_promo: False,
                        Accounts.wrong_refresh_token: False
                    }
                    ).where(Accounts.id == account_id)
                else:
                    coupon = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(16))
                    sql = update(Accounts).values({
                        Accounts.user_id: None,
                        Accounts.is_deleted: False,
                        Accounts.wrong_activation_promo: False,
                        Accounts.wrong_refresh_token: False,
                        Accounts.coupon: coupon
                    }
                    ).where(Accounts.id == account_id)

                await session.execute(sql)
                await session.commit()
                return coupon

    async def updateAccountFunctionalityByAccountId(self, account_id: int, account_functionality: int):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Accounts).values(
                    {
                        Accounts.account_functionality: account_functionality
                    }
                ).where(Accounts.id == account_id)
                await session.execute(sql)
                await session.commit()
