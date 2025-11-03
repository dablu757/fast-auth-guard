from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from typing import Union, Tuple
from app.core.config import settings


class TokenService:
    def __init__(self):
        self.secret = settings.JWT_SECRET
        self.algorithm = settings.JWT_ALGORITHM
        self.access_expire = settings.JWT_ACCESS_TOKEN_EXPIRES_MINUTES
        self.refresh_expire = settings.JWT_REFRESH_TOKEN_EXPIRES_DAYS

    def create_access_token(self, subject: Union[str, int]) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_expire)
        payload = {"sub": str(subject), "exp": expire, "type": "access"}
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def create_refresh_token(self, subject: Union[str, int]) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_expire)
        payload = {"sub": str(subject), "exp": expire, "type": "refresh"}
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self.secret, algorithms=[self.algorithm])
        except JWTError as e:
            raise JWTError("Invalid or expired token") from e

    def generate_tokens(self, user_id: Union[str, int]) -> Tuple[str, str]:
        """
        Returns (access_token, refresh_token)
        """
        return (
            self.create_access_token(user_id),
            self.create_refresh_token(user_id),
        )

    def verify_refresh_token(self, token: str) -> Union[str, None]:
        try:
            payload = self.decode_token(token)
            if payload.get("type") != "refresh":
                return None
            return payload.get("sub")
        except JWTError:
            return None
