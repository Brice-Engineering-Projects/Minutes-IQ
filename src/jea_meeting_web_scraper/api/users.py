"""
src/jea_meeting_web_scraper/api/users.py
------------------------------------------

API endpoints for user management in the JEA Meeting Web Scraper application.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from jea_meeting_web_scraper.auth.dependencies import get_current_user
from jea_meeting_web_scraper.db.client import get_db_connection
from jea_meeting_web_scraper.db.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])

# -------------------------
# Schemas
# -------------------------


class User(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


# -------------------------
# Dependencies
# -------------------------


def get_user_repository() -> UserRepository:
    """Provides a UserRepository instance with a fresh DB connection."""
    conn = get_db_connection()
    return UserRepository(conn.__enter__())


UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]
CurrentUserDep = Annotated[dict[str, Any], Depends(get_current_user)]


# -------------------------
# Routes
# -------------------------


@router.post("/", response_model=User)
async def create_user(
    user: UserCreate,
    user_repo: UserRepoDep,
):
    if user_repo.get_user_by_username(user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    return user_repo.create_user(user.username, user.email, user.password)  # type: ignore[attr-defined]


@router.get("/", response_model=list[User])
async def read_users(
    current_user: CurrentUserDep,
    user_repo: UserRepoDep,
    skip: int = 0,
    limit: int = 10,
):
    return user_repo.get_users(skip=skip, limit=limit)  # type: ignore[attr-defined]


@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: int,
    current_user: CurrentUserDep,
    user_repo: UserRepoDep,
):
    user = user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", response_model=User)
async def delete_user(
    user_id: int,
    current_user: CurrentUserDep,
    user_repo: UserRepoDep,
):
    user = user_repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_repo.delete_user(user_id)  # type: ignore[attr-defined]
