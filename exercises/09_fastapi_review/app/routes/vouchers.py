import hashlib
import hmac
import logging
import sqlite3

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.config import settings
from app.database import get_db
from app.schemas import PointsWebhook, RedeemRequest, RedeemResponse
from app.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["vouchers"])


async def _fraud_check(user_id: int, code: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(settings.fraud_check_url, json={"user_id": user_id, "code": code})
        return response.json().get("allowed", True)
    except Exception:
        return True


@router.post("/vouchers/redeem", response_model=RedeemResponse)
async def redeem_voucher(
    body: RedeemRequest,
    user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> RedeemResponse:
    voucher = db.execute(
        "SELECT * FROM vouchers WHERE code = ? AND user_id = ?",
        (body.code, user["id"]),
    ).fetchone()
    if voucher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voucher not found")
    if voucher["used"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Voucher already used")

    points = db.execute("SELECT points FROM users WHERE id = ?", (user["id"],)).fetchone()["points"]
    if points < voucher["cost_points"]:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Not enough points")

    if not await _fraud_check(user["id"], body.code):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Redemption blocked")

    remaining = points - voucher["cost_points"]
    db.execute("UPDATE users SET points = ? WHERE id = ?", (remaining, user["id"]))
    db.execute("UPDATE vouchers SET used = 1 WHERE code = ?", (body.code,))
    db.commit()

    logger.info("voucher %s redeemed by user %s", body.code, user["id"])
    return RedeemResponse(code=body.code, value=voucher["value"], remaining_points=remaining)


@router.post("/webhooks/points", status_code=status.HTTP_204_NO_CONTENT)
async def partner_points_webhook(
    request: Request,
    x_signature: str = Header(),
    db: sqlite3.Connection = Depends(get_db),
) -> None:
    raw = await request.body()
    expected = hmac.new(settings.partner_webhook_secret.encode(), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(x_signature, expected):
        logger.warning("invalid webhook signature")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    body = PointsWebhook.model_validate_json(raw)
    db.execute("UPDATE users SET points = points + ? WHERE id = ?", (body.points, body.user_id))
    db.commit()
