from sqlalchemy import Column, BigInteger, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped

from db.base import BaseModel, CleanModel
from . import Users
from .accounts import Accounts


class Presents(BaseModel, CleanModel):
    """Таблица аккаунтов"""
    __tablename__ = 'presents'

    account_id = Column(BigInteger, ForeignKey('accounts.id'), nullable=False)
    account: Mapped[Accounts] = relationship("Accounts", backref=__tablename__, cascade='all', lazy='subquery')

    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True)
    users: Mapped[Users] = relationship("Users", backref=__tablename__, cascade='all', lazy='subquery')

    is_active = Column(Boolean, default=False)

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
