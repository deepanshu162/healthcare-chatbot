import logging
from fastapi import APIRouter, Depends, HTTPException, status

from backend.models.user_models import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from backend.services.auth_service import (
    auth_service,
    get_current_user,
)

logger = logging.getLogger("healthai.routes.auth")

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new HealthAI account",
    description="Creates a new user profile and returns an initial JWT authentication token."
)
async def register(request: UserRegisterRequest) -> TokenResponse:
    """Register new user with name, email, and password."""
    user = await auth_service.register_user(
        name=request.name,
        email=request.email,
        password=request.password
    )

    access_token = auth_service.create_access_token(
        user_id=user["id"],
        email=user["email"]
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            created_at=user.get("created_at")
        )
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login to HealthAI account",
    description="Authenticates user credentials and returns a JWT bearer access token."
)
async def login(request: UserLoginRequest) -> TokenResponse:
    """Authenticate user with email and password."""
    user = await auth_service.authenticate_user(
        email=request.email,
        password=request.password
    )

    access_token = auth_service.create_access_token(
        user_id=user["id"],
        email=user["email"]
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            created_at=user.get("created_at")
        )
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Returns profile information for the authenticated user."
)
async def get_me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    """Return currently authenticated user."""
    return UserResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        created_at=current_user.get("created_at")
    )
