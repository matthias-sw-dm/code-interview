import logging
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.schemas import UserPublic
from app.security import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserPublic], dependencies=[Depends(require_admin)])
async def list_users(db: sqlite3.Connection = Depends(get_db)) -> list[UserPublic]:
    rows = db.execute("SELECT * FROM users ORDER BY id").fetchall()
    return [UserPublic(**dict(r)) for r in rows]


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: int,
    admin: dict = Depends(require_admin),
    db: sqlite3.Connection = Depends(get_db),
) -> None:
    cursor = db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    logger.info("user %s deactivated by %s", user_id, admin["email"])
