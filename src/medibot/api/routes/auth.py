from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from medibot.auth.jwt_handler import create_access_token
from medibot.auth.users import authenticate_user
from medibot.models.requests import LoginRequest
from medibot.models.responses import TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse, tags=["auth"])
def login_json(request: LoginRequest):
    """Authenticate via JSON payload and return a JWT access token."""
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return TokenResponse(access_token=token, role=user["role"])


@router.post("/token", response_model=TokenResponse, tags=["auth"], include_in_schema=False)
def login_oauth2_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate via OAuth2 Form data (used natively by Swagger UI Authorize button)."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return TokenResponse(access_token=token, role=user["role"])
