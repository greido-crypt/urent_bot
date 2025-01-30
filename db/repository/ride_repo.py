import datetime
from typing import List

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import Rides


class RidesRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_ride(
            self,
            account_id: int,
            rate_id: str,
            bot_id: int,
            finished_time: datetime.datetime,
            city: str
    ):
        async with self.session_maker() as session:
            async with session.begin():
                ride = Rides(
                    account_id=account_id,
                    rate_id=rate_id,
                    finished_time=finished_time,
                    bot_id=bot_id,
                    city=city
                )
                session.add(ride)

    async def get_all_rides_not_finished(self) -> List[Rides]:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Rides).where(Rides.upd_date == None)
                sql_res = await session.execute(sql)
                return sql_res.scalars().all()

    async def get_ride_by_id(self, ride_id: int) -> Rides | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Rides).where(Rides.id == ride_id)
                sql_res = await session.execute(sql)
                return sql_res.scalars().one_or_none()

    async def update_upd_date(self, ride_id: int) -> None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Rides).values(
                    {
                        Rides.upd_date: func.now()
                    }
                ).where(Rides.id == ride_id)
                await session.execute(sql)
                await session.commit()

    async def update_upd_date_by_account_id(self, account_id: int) -> None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Rides).values(
                    {
                        Rides.upd_date: func.now()
                    }
                ).where(Rides.account_id == account_id)
                await session.execute(sql)
                await session.commit()

    async def get_all_rides(self, finished=False) -> List[Rides]:
        async with self.session_maker() as session:
            async with session.begin():
                if not finished:
                    sql = select(Rides).where(Rides.upd_date == None)
                    sql_res = await session.execute(sql)
                    return sql_res.scalars().all()

    async def get_ride_by_rate_id(self, rate_id: str) -> Rides | None:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Rides).where(Rides.rate_id == rate_id)
                sql_res = await session.execute(sql)
                results = sql_res.scalars().all()
                try:
                    return results[-1]
                except IndexError:
                    return None
