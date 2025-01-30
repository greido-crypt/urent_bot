import secrets
import string

from fastapi import APIRouter, Body

from db.repository import account_repository
from web_app.internal.schemas import UploadSchema, ResponseUploadAccount

router = APIRouter(
    prefix="/api/v1",
)


@router.get("/get_profile")
async def get_profile():
    return {
        "phoneNumber": "+79689134548",
        "balance": "987",
        "activePromoAction": "50% скидка на 2 поездки"
    }


@router.get("/get_scooter_info")
async def get_scooter_info():
    return {
        "scooterCharge": 18,
        "scooterName": "VK1232",
        "scooterId": "S.123123",
        "startRideButton": "Поминутный | 50 + 7.99",
        "maxRideInMinutes": "Поездка автоматически завершится через 30 мин."
    }


@router.post("/upload_account")
async def upload_account(account_data: UploadSchema = Body(...)):
    coupon = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(16))
    await account_repository.add_code(
        access_token=account_data.access_token,
        refresh_token=account_data.refresh_token,
        promo_code=account_data.promo_code,
        phone_number=account_data.phone_number,
        ya_token=account_data.ya_token,
        coupon=coupon,
        fake_points=account_data.fake_points,
        fake_free_rides=account_data.fake_free_rides,
        account_functionality=account_data.account_functionality
    )
    return ResponseUploadAccount(coupon=coupon)
