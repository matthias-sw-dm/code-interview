import logging
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.security import create_access_token, hash_password, verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: sqlite3.Connection = Depends(get_db)) -> TokenResponse:
    logger.info("login attempt payload=%s", body.model_dump())

    user = db.execute("SELECT * FROM users WHERE email = ?", (body.email,)).fetchone()
    if user is None or not verify_password(body.password, user["password_hash"]) or not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return TokenResponse(access_token=create_access_token(user["id"], user["email"], user["role"]))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: sqlite3.Connection = Depends(get_db)) -> TokenResponse:
    cursor = db.execute(
        "INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)",
        (body.email.lower(), body.name, hash_password(body.password)),
    )
    db.commit()
    return TokenResponse(access_token=create_access_token(cursor.lastrowid, body.email, "customer"))
