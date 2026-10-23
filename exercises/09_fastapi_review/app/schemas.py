from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str = Field(max_length=254)
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=254)
    role: str | None = None


class UserPublic(BaseModel):
    id: int
    email: str
    name: str
    role: str
    points: int


class Order(BaseModel):
    id: int
    user_id: int
    total: float
    status: str
    shipping_address: str
    created_at: str


class RedeemRequest(BaseModel):
    code: str = Field(min_length=1, max_length=32)


class RedeemResponse(BaseModel):
    code: str
    value: float
    remaining_points: int


class PointsWebhook(BaseModel):
    user_id: int
    points: int = Field(gt=0)
    reference: str
