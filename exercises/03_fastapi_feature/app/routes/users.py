from fastapi import APIRouter, Depends

from app.auth.api_key import verify_api_key
from app.models.user import UserResponse

router = APIRouter(tags=["users"], dependencies=[Depends(verify_api_key)])


def _log_request() -> None:
    # TODO: log method, path and any extra context (e.g. query params or body summary)
    pass


@router.get("/", response_model=list[UserResponse])
async def get_users() -> list[UserResponse]:
    # TODO: add _log_request as a background task
    # TODO: query users from the database with limit and offset
    return []


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user() -> UserResponse:
    # TODO: add _log_request as a background task
    # TODO: create a User ORM instance from user data, persist it, and return it
    pass
