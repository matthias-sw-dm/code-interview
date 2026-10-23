import sqlite3

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.schemas import UserPublic, UserUpdate
from app.security import get_current_user

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)])


@router.get("/me", response_model=UserPublic)
async def read_me(user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)) -> UserPublic:
    row = db.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    return UserPublic(**dict(row))


@router.patch("/me", response_model=UserPublic)
async def update_me(
    body: UserUpdate,
    user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
) -> UserPublic:
    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        db.execute(f"UPDATE users SET {field} = ? WHERE id = ?", (value, user["id"]))
    db.commit()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    return UserPublic(**dict(row))


@router.get("/search", response_model=list[UserPublic])
async def search_users(
    q: str = Query(min_length=2),
    db: sqlite3.Connection = Depends(get_db),
) -> list[UserPublic]:
    rows = db.execute("SELECT * FROM users WHERE name LIKE ? AND is_active = 1", (f"%{q}%",)).fetchall()
    return [UserPublic(**dict(r)) for r in rows]
