from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str):
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def create_or_update_oauth_user(self, email: str, full_name: str, provider: str, sub: str):
        user = await self.get_by_email(email)
        if user:
            # Update provider info
            if not user.oauth_accounts:
                user.oauth_accounts = {}
            user.oauth_accounts[provider] = {"sub": sub}
        else:
            user = User(
                email=email,
                full_name=full_name,
                oauth_accounts={provider: {"sub": sub}},
            )
            self.db.add(user)

        await self.db.commit()
        await self.db.refresh(user)
        return user
