"""Authentication middleware to extract user from session."""
from fastapi import Request, HTTPException
from typing import Optional
import jwt
import os


async def get_user_from_request(request: Request) -> Optional[str]:
    """
    Extract user ID from request.
    In production, this should verify JWT token from NextAuth session.
    For now, we'll use a header or query parameter.
    """
    # Try to get from header (set by frontend after login)
    user_id = request.headers.get("X-User-Id")
    if user_id:
        return user_id
    
    # Try to get from query parameter
    user_id = request.query_params.get("user_id")
    if user_id:
        return user_id
    
    return None


def verify_nextauth_token(token: str) -> Optional[dict]:
    """
    Verify NextAuth JWT token.
    This is a placeholder - in production, verify against NextAuth secret.
    """
    try:
        secret = os.getenv("NEXTAUTH_SECRET")
        if not secret:
            return None
        
        # Decode token (NextAuth uses HS256)
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except Exception:
        return None

