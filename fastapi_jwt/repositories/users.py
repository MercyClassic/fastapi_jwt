from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from fastapi_jwt.exceptions.jwt import FailGetAttribute


class UserRepository:
    model = None

    def __init__(self, session: AsyncSession, username_field: str):
        self.session = session
        self.username_field = getattr(self.model, username_field, None)
        if not self.username_field:
            raise FailGetAttribute(username_field, self.model)

    async def get_info_for_authenticate(self, username_field: str):
        load_only_fields = [
            self.model.id,
            self.username_field,
            self.model.password,
        ]
        if hasattr(self.model, 'is_active'):
            load_only_fields.append(self.model.is_active)
        query = (
            select(self.model)
            .where(self.username_field == username_field)
            .options(
                load_only(*load_only_fields),
            )
        )
        result = await self.session.execute(query)
        return result.scalar()
