from __future__ import annotations

"""Firebase email/password sign-in to mint an ID token for API tests.

Captic Agent verifies a Firebase ID token on every request
(Authorization: Bearer <token>). To call /chat, /models, /history in tests we
sign the dedicated test account in via Firebase's public REST API and use the
returned idToken as the bearer token — exactly what the React app does.

Only the *Web API key* is needed (embeddable, not a service-account secret).
"""

from typing import Optional

import httpx

_SIGN_IN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"


class FirebaseAuthError(RuntimeError):
    pass


def get_id_token(
    api_key: str,
    email: str,
    password: str,
    *,
    timeout_seconds: float = 20.0,
) -> str:
    """Return a Firebase ID token for the given account, or raise FirebaseAuthError."""
    if not (api_key and email and password):
        raise FirebaseAuthError("Firebase API key, email, and password are all required.")

    resp = httpx.post(
        _SIGN_IN_URL,
        params={"key": api_key},
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=timeout_seconds,
    )
    if resp.status_code != 200:
        # Firebase returns {"error": {"message": "INVALID_PASSWORD" | "EMAIL_NOT_FOUND" | ...}}
        detail: Optional[str] = None
        try:
            detail = resp.json().get("error", {}).get("message")
        except Exception:  # noqa: BLE001
            detail = resp.text[:300]
        raise FirebaseAuthError(f"Firebase sign-in failed ({resp.status_code}): {detail}")

    token = resp.json().get("idToken")
    if not token:
        raise FirebaseAuthError("Firebase sign-in succeeded but no idToken was returned.")
    return str(token)
