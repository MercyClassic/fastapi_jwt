from sqlalchemy import insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_jwt.repositories.jwt.base import JWTBaseRepository


class JWTRepository(JWTBaseRepository):
    model = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_refresh_token(self, user_id: int, token: str) -> None:
        stmt = insert(self.model).values(user_id=user_id, token=token)
        await self.session.execute(stmt)
        await self.session.commit()

    async def delete_refresh_token(self, token: str) -> int | None:
        stmt = (
            delete(self.model)
            .where(self.model.token == token)
            .returning(self.model.id)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar()

    async def delete_all_user_refresh_tokens(self, user_id: int) -> None:
        stmt = delete(self.model).where(self.model.user_id == user_id)
        await self.session.execute(stmt)
        await self.session.commit()
