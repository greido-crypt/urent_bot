from sqlalchemy import Column, Boolean, BigInteger, ForeignKey, String, Float
from sqlalchemy.orm import relationship, Mapped

from db.base import CleanModel, BaseModel
from .users import Users


class Accounts(BaseModel, CleanModel):
    """Таблица аккаунтов"""
    __tablename__ = 'accounts'

    phone_number = Column(String, nullable=False, unique=True)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)

    coupon = Column(String, nullable=False, unique=True)

    fake_points = Column(Float, nullable=False, default=0.0)
    fake_free_rides = Column(BigInteger, nullable=False, default=0)

    ya_token = Column(String)

    promo_code = Column(String, nullable=True)
    account_functionality = Column(BigInteger, nullable=False, default=0)
    # 0 - поездка по промокодам
    # 1 - поездка по баллам
    # 2 - поездка по баллам + промокод
    # 3 - поездка за деньгу

    is_card_linked = Column(Boolean, nullable=False, default=False)  # Привязана ли карта
    is_promo_code_activated = Column(Boolean, nullable=False, default=False)  # Активирован ли промокод
    is_deleted = Column(Boolean, default=False)
    wrong_activation_promo = Column(Boolean, default=False)
    wrong_refresh_token = Column(Boolean, default=False)


    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=True)
    user: Mapped[Users] = relationship("Users", backref=__tablename__, cascade='all', lazy='subquery')

    @property
    def stats(self) -> str:
        """

        :return:
        """
        return ""

    def __str__(self) -> str:
        return (
            f"<Accounts:\n"
            f"  ID: {self.id}\n"
            f"  Phone Number: {self.phone_number}\n"
            f"  Access Token: {self.access_token}\n"
            f"  Refresh Token: {self.refresh_token}\n"
            f"  Coupon: {self.coupon}\n"
            f"  Fake Points: {self.fake_points}\n"
            f"  Fake Free Rides: {self.fake_free_rides}\n"
            f"  Is Deleted: {self.is_deleted}\n"
            f"  Wrong Activation Promo: {self.wrong_activation_promo}\n"
            f"  Wrong Refresh Token: {self.wrong_refresh_token}\n"
            f"  Ya Token: {self.ya_token}\n"
            f"  Promo Code: {self.promo_code}\n"
            f"  Account Functionality: {self.account_functionality}\n"
            f"  Is Card Linked: {self.is_card_linked}\n"
            f"  Is Promo Code Activated: {self.is_promo_code_activated}\n"  # Вывод информации об активации промокода
            f"  User ID: {self.user_id}\n"
            f">"
        )

    def __repr__(self):
        return self.__str__()
