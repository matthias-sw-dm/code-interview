import csv
import io
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.schemas import Order
from app.security import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[Order])
async def list_orders(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> list[Order]:
    rows = db.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (user["id"], limit, offset),
    ).fetchall()
    return [Order(**dict(r)) for r in rows]


@router.get("/export")
async def export_orders(db: sqlite3.Connection = Depends(get_db)) -> StreamingResponse:
    rows = db.execute(
        "SELECT o.id, u.email, u.name, o.total, o.status, o.shipping_address, o.created_at "
        "FROM orders o JOIN users u ON u.id = o.user_id"
    ).fetchall()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "email", "name", "total", "status", "shipping_address", "created_at"])
    writer.writerows(rows)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="text/csv")


@router.get("/{order_id}", response_model=Order)
async def get_order(
    order_id: int,
    user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> Order:
    row = db.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, user["id"])).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return Order(**dict(row))
