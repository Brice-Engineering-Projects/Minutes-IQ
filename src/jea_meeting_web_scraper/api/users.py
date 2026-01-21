"""
src/jea_meeting_web_scraper/api/users.py
------------------------------------------

API endpoints for user management in the JEA Meeting Web Scraper application.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.jea_meeting_web_scraper.auth import get_current_user
from src.jea_meeting_web_scraper.database import UserDB, get_user_db

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
# Dependency aliases
# -------------------------

UserDBDep = Annotated[UserDB, Depends(get_user_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


# -------------------------
# Routes
# -------------------------


@router.post("/", response_model=User)
async def create_user(
    user: UserCreate,
    db: UserDBDep,
):
    if db.get_user_by_username(user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    return db.create_user(user.username, user.email, user.password)


@router.get("/", response_model=list[User])
async def read_users(
    current_user: CurrentUserDep,
    db: UserDBDep,
    skip: int = 0,
    limit: int = 10,
):
    return db.get_users(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: int,
    current_user: CurrentUserDep,
    db: UserDBDep,
):
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", response_model=User)
async def delete_user(
    user_id: int,
    current_user: CurrentUserDep,
    db: UserDBDep,
):
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return db.delete_user(user_id)
