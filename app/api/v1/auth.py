from fastapi import APIRouter, Depends, Request, HTTPException
from starlette.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.user_repo import UserRepository
from app.services.token_service import TokenService
from app.services.auth_service import oauth


router = APIRouter(prefix="/auth", tags=["Auth"])
token_service = TokenService()


@router.get("/login/{provider}")
async def oauth_login(provider: str, request: Request):
    if provider not in oauth:
        raise HTTPException(status_code=404, detail="Provider not supported")

    redirect_uri = request.url_for("auth_callback", provider=provider)
    return await oauth[provider].authorize_redirect(request, redirect_uri)


@router.get("/callback/{provider}")
async def auth_callback(provider: str, request: Request, db: AsyncSession = Depends(get_db)):
    token = await oauth[provider].authorize_access_token(request)
    user_info = token.get("userinfo") or await oauth[provider].parse_id_token(request, token)

    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to fetch user info")

    repo = UserRepository(db)
    user = await repo.create_or_update_oauth_user(
        email=user_info["email"],
        full_name=user_info.get("name", ""),
        provider=provider,
        sub=user_info.get("sub", user_info.get("id", "")),
    )

    access_token, refresh_token = token_service.generate_tokens(user.id)
    response = JSONResponse({"access_token": access_token, "refresh_token": refresh_token})
    return response


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    sub = token_service.verify_refresh_token(refresh_token)
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access_token, new_refresh_token = token_service.generate_tokens(sub)
    return {"access_token": access_token, "refresh_token": new_refresh_token}
