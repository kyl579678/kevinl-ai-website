#!/usr/bin/env python3
"""Simple authentication for AI endpoints."""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Header


# Simple password-based auth
# In production, use proper password hashing (bcrypt/argon2)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "demo123")  # Change this!

# Session tokens (in-memory for simplicity, use Redis in production)
_active_sessions: dict[str, datetime] = {}
SESSION_DURATION = timedelta(hours=24)


def create_session() -> str:
    """Create a new session token."""
    token = secrets.token_urlsafe(32)
    _active_sessions[token] = datetime.now() + SESSION_DURATION
    return token


def verify_session(token: str) -> bool:
    """Check if a session token is valid."""
    if token not in _active_sessions:
        return False
    
    expiry = _active_sessions[token]
    if datetime.now() > expiry:
        # Expired
        del _active_sessions[token]
        return False
    
    return True


def verify_password(password: str) -> bool:
    """Verify login password."""
    return password == ADMIN_PASSWORD


def require_auth(authorization: Optional[str] = Header(None)) -> None:
    """FastAPI dependency to require authentication."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Expected format: "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    if not verify_session(token):
        raise HTTPException(status_code=401, detail="Invalid or expired session")


def cleanup_expired_sessions():
    """Remove expired sessions (call periodically)."""
    now = datetime.now()
    expired = [token for token, expiry in _active_sessions.items() if now > expiry]
    for token in expired:
        del _active_sessions[token]
