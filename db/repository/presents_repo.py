from typing import List, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import Presents


class PresentsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def addPresent(self, account_id: int) -> bool:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                present = Presents(account_id=account_id)
                try:
                    session.add(present)
                except Exception as e:
                    print(e)
                    return False
                return True

    async def addPresents(self, accounts: List[Presents]):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                try:
                    session.add_all(accounts)
                except Exception as e:
                    print(e)
                    return False
                return True

    async def getPresentById(self, present_id: int) -> Presents | None:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Presents).where(Presents.id == present_id)
                query = await session.execute(sql)
                return query.scalars().one_or_none()

    async def getPresents(self, is_active: bool = False) -> Sequence[Presents]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Presents).where(Presents.is_active == is_active)
                query = await session.execute(sql)
                return query.scalars().all()

    async def updatePresentIsActiveStatusById(self, present_id: int, is_active: bool = True):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Presents).values(
                    {
                        Presents.is_active: is_active
                    }
                ).where(Presents.id == present_id)
                await session.execute(sql)
                await session.commit()

    async def getPresentsByUserId(self, user_id: int) -> Sequence[Presents]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Presents).where(Presents.user_id == user_id)
                query = await session.execute(sql)
                return query.scalars().all()

    async def updatePresentUserIdByPresentId(self, present_id: int, user_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Presents).values(
                    {
                        Presents.user_id: user_id
                    }
                ).where(Presents.id == present_id)
                await session.execute(sql)
                await session.commit()
