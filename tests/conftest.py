import asyncio
from typing import AsyncGenerator

import pytest
from sqlalchemy import ForeignKey, Integer, Boolean, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import NullPool

from models.jwt import RefreshToken

DATABASE_URL_TEST = 'postgresql+asyncpg://postgres:postgres@localhost:5432/test_db'

engine_test = create_async_engine(DATABASE_URL_TEST, poolclass=NullPool)
async_sessionmaker = sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class TestAccountTable(Base):
    __tablename__ = 'account'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class TestRefreshTokenTable(Base, RefreshToken):
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id'), nullable=False)


Base.metadata.bind = engine_test


@pytest.fixture(autouse=True, scope='module')
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope='module')
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='module')
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with async_sessionmaker() as session:
        yield session
