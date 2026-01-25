"""
Admin routes for authorization code management.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from jea_meeting_web_scraper.auth.dependencies import (
    get_auth_code_service,
    get_current_admin_user,
)
from jea_meeting_web_scraper.db.auth_code_service import AuthCodeService

router = APIRouter(prefix="/admin/auth-codes", tags=["Admin - Authorization Codes"])


# Request/Response models
class CreateAuthCodeRequest(BaseModel):
    """Request model for creating an authorization code."""

    expires_in_days: int | None = Field(
        default=7, description="Days until code expires (null = never)"
    )
    max_uses: int = Field(default=1, ge=1, description="Maximum number of uses")
    notes: str | None = Field(default=None, description="Optional notes about the code")


class AuthCodeResponse(BaseModel):
    """Response model for authorization code."""

    code_id: int
    code: str
    code_formatted: str | None = None
    created_by: int
    created_at: int
    expires_at: int | None
    max_uses: int
    current_uses: int
    is_active: bool
    notes: str | None


class AuthCodeListResponse(BaseModel):
    """Response model for listing authorization codes."""

    codes: list[dict]
    total: int


@router.post("", response_model=AuthCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_auth_code(
    request: CreateAuthCodeRequest,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    auth_code_service: Annotated[AuthCodeService, Depends(get_auth_code_service)],
):
    """
    Create a new authorization code.

    Only admins can create authorization codes.
    """
    code_data = auth_code_service.create_code(
        created_by=admin_user["user_id"],
        expires_in_days=request.expires_in_days,
        max_uses=request.max_uses,
        notes=request.notes,
    )

    return AuthCodeResponse(
        code_id=code_data["code_id"],
        code=code_data["code"],
        code_formatted=code_data.get("code_formatted"),
        created_by=code_data["created_by"],
        created_at=code_data["created_at"],
        expires_at=code_data["expires_at"],
        max_uses=code_data["max_uses"],
        current_uses=code_data["current_uses"],
        is_active=bool(code_data["is_active"]),
        notes=code_data["notes"],
    )


@router.get("", response_model=AuthCodeListResponse)
async def list_auth_codes(
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    auth_code_service: Annotated[AuthCodeService, Depends(get_auth_code_service)],
    status_filter: str = "active",
    limit: int = 100,
    offset: int = 0,
):
    """
    List authorization codes with filtering.

    Query parameters:
    - status: Filter by status ("active", "expired", "used", "revoked", "all")
    - limit: Maximum number of results (default: 100)
    - offset: Pagination offset (default: 0)

    Only admins can list authorization codes.
    """
    codes = auth_code_service.list_codes(
        status=status_filter, limit=limit, offset=offset
    )

    return AuthCodeListResponse(
        codes=codes,
        total=len(codes),
    )


@router.delete("/{code_id}", status_code=status.HTTP_200_OK)
async def revoke_auth_code(
    code_id: int,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    auth_code_service: Annotated[AuthCodeService, Depends(get_auth_code_service)],
):
    """
    Revoke an authorization code.

    Only admins can revoke authorization codes.
    """
    result = auth_code_service.revoke_code(code_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Authorization code with ID {code_id} not found",
        )

    return {
        "message": "Authorization code revoked successfully",
        "code_id": code_id,
    }


@router.get("/{code_id}/usage")
async def get_code_usage_history(
    code_id: int,
    admin_user: Annotated[dict, Depends(get_current_admin_user)],
    auth_code_service: Annotated[AuthCodeService, Depends(get_auth_code_service)],
):
    """
    Get usage history for a specific authorization code.

    Only admins can view code usage history.
    """
    history = auth_code_service.get_code_usage_history(code_id)

    return {
        "code_id": code_id,
        "usage_history": history,
        "total_uses": len(history),
    }
