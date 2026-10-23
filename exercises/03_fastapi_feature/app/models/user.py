from pydantic import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import MappedColumn

from app.utils.database import Base


class User(Base):
    __tablename__ = "users"

    # TODO: Implement user properties
    dummy_id = MappedColumn(String, primary_key=True)


class UserCreate(BaseModel):
    # TODO: Implement payload schema
    pass


class UserResponse(BaseModel):
    # TODO: Implement payload schema
    pass
