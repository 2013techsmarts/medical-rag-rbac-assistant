from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from medibot.auth.jwt_handler import decode_access_token

# OAuth2 scheme looking for token in Bearer headers
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_role(token: str = Depends(oauth2_scheme)) -> str:
    """
    FastAPI dependency that validates the JWT token from authorization headers
    and extracts the authenticated user's role.
    
    Args:
        token: Extracted Bearer token.
        
    Returns:
        Role string (e.g. 'doctor', 'nurse', etc.).
        
    Raises:
        HTTPException 401: If token is invalid, expired, or role missing.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
        
    role: str = payload.get("role")
    if not role:
        raise credentials_exception
        
    return role
