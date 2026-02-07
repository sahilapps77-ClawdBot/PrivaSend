"""Authentication utilities using Supabase JWT."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from tools.supabase_client import SUPABASE_ANON_KEY

# Configure logging
log = logging.getLogger("privasend.auth")

# JWT configuration for Supabase
JWT_ALGORITHM = "HS256"

# Security scheme
security = HTTPBearer(auto_error=False)


class User(BaseModel):
    """Authenticated user model."""
    id: str
    email: str
    aud: str


class AuthError(Exception):
    """Authentication error."""
    pass


def verify_jwt_token(token: str) -> dict:
    """
    Verify a Supabase JWT token.
    
    Args:
        token: JWT access token from Supabase
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthError: If token is invalid or expired
    """
    try:
        # Decode token without verification first to check structure
        payload = jwt.decode(
            token,
            SUPABASE_ANON_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"verify_aud": False}  # Supabase uses custom aud
        )
        return payload
    except JWTError as e:
        log.error(f"JWT verification failed: {e}")
        raise AuthError(f"Invalid token: {e}")
    except Exception as e:
        log.error(f"Unexpected error during JWT verification: {e}")
        raise AuthError("Token verification failed")


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> User:
    """
    FastAPI dependency to get current authenticated user.
    
    Args:
        credentials: HTTP Authorization header with Bearer token
        
    Returns:
        User object if authenticated
        
    Raises:
        HTTPException: 401 if not authenticated
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")
    
    token = credentials.credentials
    
    try:
        payload = verify_jwt_token(token)
        
        # Extract user info from token
        user_id = payload.get("sub")
        email = payload.get("email")
        aud = payload.get("aud")
        
        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Invalid token: missing user information")
        
        return User(id=user_id, email=email, aud=aud)
        
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


async def require_auth(request: Request) -> User:
    """
    Require authentication for a request.
    Can be used as a dependency in FastAPI endpoints.
    """
    # Get Authorization header
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")
    
    token = auth_header.replace("Bearer ", "")
    
    try:
        payload = verify_jwt_token(token)
        
        user_id = payload.get("sub")
        email = payload.get("email")
        aud = payload.get("aud")
        
        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Invalid token: missing user information")
        
        # Attach user to request state for access in endpoints
        request.state.user = User(id=user_id, email=email, aud=aud)
        
        return request.state.user
        
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    For endpoints that work with or without auth.
    """
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None
