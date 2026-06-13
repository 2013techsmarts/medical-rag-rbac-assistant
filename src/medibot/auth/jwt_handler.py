from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

from medibot.config.settings import settings

SECRET_KEY = settings.jwt_secret
ALGORITHM = settings.jwt_algorithm
EXPIRE_MINUTES = settings.jwt_expire_minutes


def create_access_token(data: dict) -> str:
    """
    Create a signed JWT access token.
    
    Args:
        data: Dict containing claims (e.g. {'sub': username, 'role': role}).
        
    Returns:
        Encoded JWT token string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT string.
        
    Returns:
        Decoded payload dict or None if invalid.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
