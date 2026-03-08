"""Email delivery helpers for authentication workflows."""

import logging
import os

import requests

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    """
    Send a password reset email via SendGrid.

    Returns True when the request is accepted by SendGrid. Returns False when
    SendGrid is not configured or when delivery fails.
    """
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL")

    if not api_key or not from_email:
        logger.info("SendGrid not configured; skipping password reset email delivery")
        return False

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "subject": "Reset your MinutesIQ password",
        "content": [
            {
                "type": "text/plain",
                "value": (
                    "We received a request to reset your password. "
                    f"Use this link to continue: {reset_link}\n\n"
                    "If you did not request this, you can ignore this email."
                ),
            }
        ],
    }

    try:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )

        if response.status_code == 202:
            return True

        logger.warning(
            "SendGrid rejected password reset email with status %s",
            response.status_code,
        )
    except requests.RequestException:
        logger.exception("Failed to send password reset email via SendGrid")

    return False
