from fastapi import Depends, HTTPException, status, Header, Security
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, Union
from uuid import UUID, uuid4
from jose import JWTError, jwt

from .models.user import UserResponse, TokenData
from .core.config import settings
from .services.auth_service import AuthService

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

# For backward compatibility during transition
async def get_current_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> UUID:
    """
    DEPRECATED: Extract and validate the current user ID from the X-User-ID header.
    This is a simple header-based approach without actual authentication.
    Only used for backward compatibility during transition to JWT auth.
    
    Args:
        x_user_id: The user ID from the X-User-ID header
        
    Returns:
        The UUID of the current user
        
    Raises:
        HTTPException: If the user ID is not provided or is invalid
    """
    if not x_user_id:
        # For development/demo purposes, use a default UUID
        # This would be removed in production
        return UUID("00000000-0000-0000-0000-000000000001")
    
    try:
        return UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

async def get_token_data(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Decode and validate a JWT token
    
    Args:
        token: The JWT token to decode
            
    Returns:
        The token data
            
    Raises:
        HTTPException: If the token is invalid or expired
    """
    auth_service = AuthService()
    return auth_service.decode_token(token)

async def get_current_user(token_data: TokenData = Depends(get_token_data)) -> UserResponse:
    """
    Get the current user from token data
    
    Args:
        token_data: The decoded token data
            
    Returns:
        The current user
            
    Raises:
        HTTPException: If the user is not found
    """
    auth_service = AuthService()
    user = await auth_service.get_user_by_id(token_data.user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        company_name=user.company_name,
        job_title=user.job_title,
        is_active=user.is_active,
        created_at=user.created_at
    )

async def get_current_active_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """
    Get the current user and verify they are active
    
    Args:
        current_user: The current user
            
    Returns:
        The current active user
            
    Raises:
        HTTPException: If the user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

# For backward compatibility during transition
async def get_current_user_id(
    current_user: UserResponse = Depends(get_current_active_user),
    x_user_id: Optional[str] = Header(None)
) -> UUID:
    """
    Get the current user ID from either JWT or header for backward compatibility
    
    Args:
        current_user: The current user from JWT
        x_user_id: The user ID from the X-User-ID header (fallback)
            
    Returns:
        The UUID of the current user
    """
    # Prefer JWT auth if available
    if current_user:
        return current_user.id
    
    # Fallback to header-based auth (for development only)
    return await get_current_user_id_from_header(x_user_id)