"""Profile API endpoints - returns HTML fragments for profile updates."""

from html import escape
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from minutes_iq.auth.dependencies import get_current_user
from minutes_iq.auth.security import verify_password
from minutes_iq.db.dependencies import get_user_repository
from minutes_iq.db.user_repository import UserRepository

router = APIRouter(prefix="/api/profile", tags=["Profile API"])


@router.put("/update-info", response_class=HTMLResponse)
async def update_profile_info(
    current_user: Annotated[dict, Depends(get_current_user)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    username: str = Form(...),
    email: str = Form(...),
):
    """Update user's username and/or email."""
    # Validate inputs
    if not username or len(username) < 3 or len(username) > 50:
        return """
        <div class="rounded-md bg-red-50 border border-red-200 p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-red-800">Validation Error</h3>
                    <p class="mt-1 text-sm text-red-700">Username must be 3-50 characters.</p>
                </div>
            </div>
        </div>
        """

    if not email or "@" not in email:
        return """
        <div class="rounded-md bg-red-50 border border-red-200 p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-red-800">Validation Error</h3>
                    <p class="mt-1 text-sm text-red-700">Please provide a valid email address.</p>
                </div>
            </div>
        </div>
        """

    # Check if anything actually changed
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in session")

    if username == current_user.get("username") and email == current_user.get("email"):
        return """
        <div class="rounded-md bg-blue-50 border border-blue-200 p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-blue-800">No Changes</h3>
                    <p class="mt-1 text-sm text-blue-700">Your profile information is already up to date.</p>
                </div>
            </div>
        </div>
        """

    # Prepare update parameters
    new_username = username if username != current_user.get("username") else None
    new_email = email if email != current_user.get("email") else None

    # Attempt update
    try:
        updated_user = user_repo.update_user(
            user_id=user_id, username=new_username, email=new_email
        )

        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Prepare success message
        changes = []
        if new_username:
            changes.append("username")
        if new_email:
            changes.append("email")

        changes_text = " and ".join(changes)

        email_note = ""
        if new_email:
            email_note = """
            <p class="mt-2 text-sm text-green-700">
                <strong>Note:</strong> An email verification link has been sent to your new address.
                Please verify to complete the change.
            </p>
            """

        return f"""
        <div class="rounded-md bg-green-50 border border-green-200 p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-green-800">Profile Updated</h3>
                    <p class="mt-1 text-sm text-green-700">
                        Your {escape(changes_text)} has been updated successfully.
                    </p>
                    {email_note}
                </div>
            </div>
        </div>
        <script>
            // Refresh page after 2 seconds to show updated info in navbar
            setTimeout(() => window.location.reload(), 2000);
        </script>
        """

    except ValueError as e:
        # Handle duplicate username/email errors
        error_msg = str(e)
        return f"""
        <div class="rounded-md bg-red-50 border border-red-200 p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-red-800">Update Failed</h3>
                    <p class="mt-1 text-sm text-red-700">{escape(error_msg)}</p>
                </div>
            </div>
        </div>
        """


@router.put("/update-password", response_class=HTMLResponse)
async def update_password(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    """Update user's password."""
    # Validate new password
    if len(new_password) < 8:
        return """
        <div class="rounded-md bg-red-50 border border-red-200 p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-red-800">Validation Error</h3>
                    <p class="mt-1 text-sm text-red-700">New password must be at least 8 characters long.</p>
                </div>
            </div>
        </div>
        """

    # Verify passwords match
    if new_password != confirm_password:
        return """
        <div class="rounded-md bg-red-50 border border-red-200 p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-red-800">Validation Error</h3>
                    <p class="mt-1 text-sm text-red-700">New password and confirmation do not match.</p>
                </div>
            </div>
        </div>
        """

    # Verify current password
    # Get current password hash from auth_credentials
    from minutes_iq.db.client import get_db_connection

    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in session")

    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT hashed_password
            FROM auth_credentials
            WHERE user_id = ? AND provider_id = 1
            """,
            (user_id,),
        )
        row = cursor.fetchone()

        if not row:
            return """
            <div class="rounded-md bg-red-50 border border-red-200 p-4">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                        </svg>
                    </div>
                    <div class="ml-3">
                        <h3 class="text-sm font-medium text-red-800">Error</h3>
                        <p class="mt-1 text-sm text-red-700">No password credentials found for this account.</p>
                    </div>
                </div>
            </div>
            """

        current_hash = row[0]

    # Verify current password
    if not verify_password(current_password, current_hash):
        return """
        <div class="rounded-md bg-red-50 border border-red-200 p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-red-800">Authentication Failed</h3>
                    <p class="mt-1 text-sm text-red-700">Current password is incorrect.</p>
                </div>
            </div>
        </div>
        """

    # Update password
    try:
        user_repo.update_password(user_id, new_password)

        return """
        <div class="rounded-md bg-green-50 border border-green-200 p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-green-800">Password Updated</h3>
                    <p class="mt-1 text-sm text-green-700">
                        Your password has been changed successfully. You can now use it to log in.
                    </p>
                </div>
            </div>
        </div>
        """

    except ValueError as e:
        error_msg = str(e)
        return f"""
        <div class="rounded-md bg-red-50 border border-red-200 p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-red-800">Update Failed</h3>
                    <p class="mt-1 text-sm text-red-700">{escape(error_msg)}</p>
                </div>
            </div>
        </div>
        """
