# User routes
from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.utils.jwt import decode_token
from app.db.models import User
from app.schemas.user_schema import UserRead

router = APIRouter(prefix="/users", tags=["users"])


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """
    Extracts and verifies the JWT token from cookies,
    decodes it, and fetches the current user from the database.
    """
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token missing. Please log in.",
        )

    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
        )

    q = await db.execute(select(User).where(User.id == user_id))
    user = q.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns details of the authenticated user.
    """
    return current_user


@router.get("/all", response_model=list[UserRead])
async def get_all_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all users.
    (In production, protect this route with role-based access control.)
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Optionally: make sure the user exists (and maybe is admin)
    q_user = await db.execute(select(User).where(User.id == user_id))
    user = q_user.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # In production: check if user.is_admin
    q_all = await db.execute(select(User))
    users = q_all.scalars().all()
    return users
