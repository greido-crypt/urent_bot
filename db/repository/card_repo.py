from typing import List

from sqlalchemy import select, update, func

from db.engine import DatabaseEngine
from db.models import Cards


class CardsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def addCard(
            self,
            number: str,
            date: str,
            cvc: str,
            user_id: int
    ) -> bool:
        async with self.session_maker() as session:
            async with session.begin():
                card = Cards(
                    number=number,
                    date=date,
                    cvc=cvc,
                    user_id=user_id
                )
                try:
                    session.add(card)
                except Exception:
                    return False
                return True

    async def getCardByCardId(self, card_id: int) -> Cards | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Cards).where(Cards.id == card_id)
                sql_res = await session.execute(sql)
                return sql_res.scalars().one_or_none()

    async def getCardByNumber(self, number: str) -> Cards | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Cards).where(Cards.number == number)
                sql_res = await session.execute(sql)
                return sql_res.scalars().one_or_none()

    async def updateCardDataById(self,
                                 card_id: int,
                                 number: str,
                                 date: str,
                                 cvc: str,
                                 user_id: int):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Cards).values(
                    {
                        Cards.number: number,
                        Cards.date: date,
                        Cards.cvc: cvc,
                        Cards.user_id: user_id,
                        Cards.is_deleted: False
                    }
                ).where(Cards.id == card_id)
                await session.execute(sql)
                await session.commit()

    async def getCardsByUserId(self, user_id: int, is_deleted: bool = False) -> List[Cards]:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Cards).where(Cards.user_id == user_id,
                                          Cards.is_deleted == is_deleted)
                sql_res = await session.execute(sql)
                return sql_res.scalars().all()

    async def updateIsDeletedByCardId(self, card_id: int, is_deleted: bool = True):
        """
        _id: card_id
        """
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Cards).values(
                    {
                        Cards.is_deleted: is_deleted
                    }
                ).where(Cards.id == card_id)
                await session.execute(sql)
                await session.commit()

    async def usePaymentSystemByCardId(self, card_id: int, payment_system_id: str):
        """
        payment_system_id: mir_pay, yoomoney, ecom_pay
        """
        async with self.session_maker() as session:
            async with session.begin():
                if payment_system_id == 'yoomoney':
                    sql = update(Cards).values(
                        {
                            Cards.yoomoney: Cards.yoomoney + 1
                        }
                    ).where(Cards.id == card_id)

                elif payment_system_id == 'ecom_pay':
                    sql = update(Cards).values(
                        {
                            Cards.ecom_pay: Cards.ecom_pay + 1
                        }
                    ).where(Cards.id == card_id)

                elif payment_system_id == 'mts_pay':
                    sql = update(Cards).values(
                        {
                            Cards.ecom_pay: Cards.ecom_pay + 1
                        }
                    ).where(Cards.id == card_id)
                try:
                    await session.execute(sql)
                    await session.commit()
                except Exception:
                    return False
                return True

    async def get_all_cards(self, is_deleted=False) -> List[Cards]:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Cards).where(Cards.is_deleted == is_deleted)
                sql_res = await session.execute(sql)
                return sql_res.scalars().all()

    async def clearPaymentsSystems(self, card_id: int) -> bool:
        async with self.session_maker() as session:
            async with session.begin():
                try:
                    sql = update(Cards).values(
                        {
                            Cards.yoomoney: 0,
                            Cards.ecom_pay: 0,
                            Cards.mts_pay: 0
                        }
                    ).where(Cards.id == card_id)
                    await session.execute(sql)
                    await session.commit()
                    return True
                except Exception as e:
                    print(e)
                    return False

    async def banCardById(self, card_id: int) -> bool:
        async with self.session_maker() as session:
            async with session.begin():
                try:
                    sql = update(Cards).values(
                        {
                            Cards.yoomoney: 4,
                            Cards.ecom_pay: 4,
                            Cards.mts_pay: 4,
                        }
                    ).where(Cards.id == card_id)
                    await session.execute(sql)
                    await session.commit()
                    return True
                except Exception as e:
                    print(e)
                    return False