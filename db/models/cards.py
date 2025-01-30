from sqlalchemy import Column, Integer, Boolean, BigInteger, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship, Mapped

from db.base import CleanModel, BaseModel
from .users import Users


class Cards(BaseModel, CleanModel):
    """Таблица карт"""
    __tablename__ = 'cards'

    number = Column(String, nullable=False)
    date = Column(String, nullable=False)
    cvc = Column(String, nullable=False)
    is_deleted = Column(Boolean, default=False)

    yoomoney = Column(Integer, default=0)
    ecom_pay = Column(Integer, default=0)
    mts_pay = Column(Integer, default=0)

    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    user: Mapped[Users] = relationship("Users", backref=__tablename__, cascade='all', lazy='subquery')

    @property
    def stats(self) -> str:
        """

        :return:
        """
        return ""

    def __str__(self) -> str:
        return f"<CardsModel:{self.id}>"

    def __repr__(self):
        return self.__str__()
