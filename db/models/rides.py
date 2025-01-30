from sqlalchemy import Column, BigInteger, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship, Mapped

from db.base import BaseModel, CleanModel
from .accounts import Accounts


class Rides(BaseModel, CleanModel):
    """Таблица аккаунтов"""
    __tablename__ = 'rides'

    rate_id = Column(String, nullable=False)
    city = Column(String, nullable=True)

    account_id = Column(BigInteger, ForeignKey('accounts.id'), nullable=False)
    account: Mapped[Accounts] = relationship("Accounts", backref=__tablename__, cascade='all', lazy='subquery')

    bot_id = Column(BigInteger, nullable=False)

    finished_time = Column(DateTime, nullable=False)

    @property
    def stats(self) -> str:
        """

        :return:
        """
        return ""

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}:{self.id}>"

    def __repr__(self):
        return self.__str__()
