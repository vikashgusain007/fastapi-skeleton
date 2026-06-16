from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User
from repositories.base import BaseRepository
from schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    Repository layer for User database queries.
    """

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Fetch a user by their email address.
        """
        result = await db.execute(select(self.model).filter(self.model.email == email))
        return result.scalars().first()


user_repository = UserRepository(User)
