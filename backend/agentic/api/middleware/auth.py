"""
Authentication middleware using MSAL for Microsoft Entra ID.
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import jwt
from jwt import PyJWKClient
import requests
from functools import lru_cache

from config.settings import get_settings

settings = get_settings()
security = HTTPBearer()


@lru_cache()
def get_signing_keys():
    """
    Get signing keys from Microsoft Entra ID.
    
    Cached to avoid repeated requests.
    """
    if not settings.azure_tenant_id:
        return None
        
    # Microsoft Entra ID OpenID configuration endpoint
    openid_config_url = (
        f"https://login.microsoftonline.com/{settings.azure_tenant_id}/"
        f"v2.0/.well-known/openid-configuration"
    )
    
    try:
        # Get OpenID configuration
        config_response = requests.get(openid_config_url)
        config_response.raise_for_status()
        config = config_response.json()
        
        # Get JWKS URI
        jwks_uri = config["jwks_uri"]
        
        # Create JWKS client
        jwks_client = PyJWKClient(jwks_uri)
        return jwks_client
        
    except Exception as e:
        print(f"Failed to get signing keys: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Validate JWT token and return user information.
    
    In development mode, returns a mock user if no valid token.
    """
    token = credentials.credentials
    
    # Development mode bypass
    if settings.is_development and not settings.azure_tenant_id:
        return {
            "sub": "dev-user-123",
            "email": "dev@stratos.ai",
            "name": "Development User",
            "tid": "dev-tenant-123"
        }
    
    # Get signing keys
    jwks_client = get_signing_keys()
    if not jwks_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not configured"
        )
    
    try:
        # Get signing key from token
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decode and validate token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.azure_client_id,
            issuer=f"https://login.microsoftonline.com/{settings.azure_tenant_id}/v2.0"
        )
        
        # Extract user information
        user_info = {
            "sub": payload.get("sub"),  # User ID
            "email": payload.get("email") or payload.get("preferred_username"),
            "name": payload.get("name"),
            "tid": payload.get("tid"),  # Tenant ID
            "roles": payload.get("roles", []),
            "groups": payload.get("groups", [])
        }
        
        return user_info
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


async def require_role(required_role: str):
    """
    Dependency to require a specific role.
    
    Usage:
        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ):
        roles = current_user.get("roles", [])
        if required_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    
    return role_checker


async def require_group(required_group: str):
    """
    Dependency to require membership in a specific group.
    
    Usage:
        @router.get("/team", dependencies=[Depends(require_group("team-id"))])
    """
    async def group_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ):
        groups = current_user.get("groups", [])
        if required_group not in groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Group membership required"
            )
        return current_user
    
    return group_checker