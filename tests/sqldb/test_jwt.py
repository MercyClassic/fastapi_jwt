import pytest
from fastapi import HTTPException
from sqlalchemy import insert, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count
from starlette.requests import Request

from fastapi_jwt.auth.jwt import decode_jwt, generate_jwt
from fastapi_jwt.exceptions.jwt import FailGetAttribute
from fastapi_jwt.managers.users import UserManager
from fastapi_jwt.schemas.jwt import AuthenticateSchema
from fastapi_jwt.repositories.jwt.sqldb import JWTRepository
from fastapi_jwt.repositories.users import UserRepository
from fastapi_jwt.services.jwt import JWTService
from fastapi_jwt.services.users import UserService
from tests.conftest import (
    TestAccountTable,
    TestRefreshTokenTable,
)
from fastapi_jwt.actions.jwt import login, refresh_access_token, logout


class OverridenUserRepository(UserRepository):
    model = TestAccountTable


class OverridenJWTRepository(JWTRepository):
    model = TestRefreshTokenTable


class JWTTests:
    @pytest.fixture(autouse=True, scope='module')
    async def setup(self, session: AsyncSession):
        stmt = insert(TestAccountTable).values(
            email='test@test.com',
            password=UserManager.make_password('test'),
        )
        await session.execute(stmt)
        await session.commit()

    @pytest.fixture(autouse=True, scope='function')
    async def clear_refresh_token_table(self, session: AsyncSession):
        stmt = delete(TestRefreshTokenTable)
        await session.execute(stmt)
        await session.commit()

    @pytest.mark.parametrize(
        'username, username_field, password, is_ok, result_count',
        [
            ('test@test.com', 'email', 'test', True, 1),
            ('test@test.com', 'email', 'fail', False, 0),
            ('fail@fail.com', 'email', 'test', False, 0),
            ('test@test.com', 'username', 'test', False, 0),
        ]
    )
    async def test_login(
            self,
            username: str,
            username_field: str,
            password: str,
            is_ok: bool,
            result_count: int,
            session: AsyncSession,
    ):
        data = AuthenticateSchema(username_field=username, input_password=password)
        jwt_service = JWTService(
            OverridenJWTRepository(
                session,
            ),
        )
        try:
            user_service = UserService(
                OverridenUserRepository(
                    session,
                    username_field=username_field,
                ),
            )
        except FailGetAttribute:
            if is_ok:
                assert False
            assert True
            return
        try:
            response = await login(data, jwt_service, user_service)
        except HTTPException:
            if is_ok:
                assert False

            await self.assert_db_token_count(session, result_count)

            assert True
            return

        self.assert_tokens(tuple(response.values()))

    @staticmethod
    def assert_tokens(tokens: tuple) -> None:
        for token in tokens:
            data = decode_jwt(
                encoded_jwt=token,
                secret='JWT',
                algorithm='HS256',
            )
            assert data.get('sub') == '1'

    @staticmethod
    async def assert_db_token_count(session: AsyncSession, result_count: int) -> None:
        query = select(count(TestRefreshTokenTable.id))
        result = await session.execute(query)
        assert result.scalar() == result_count

    @pytest.mark.parametrize(
        'token, no_exception',
        [
            ('wrong token', False),
            (None, False),
            (
                    generate_jwt(
                        data={'sub': 1},
                        lifetime_seconds=3,
                        secret='JWT',
                        algorithm='HS256',
                    ), True,
            ),
        ]
    )
    async def test_refresh_access_token(
            self,
            token: str | None,
            no_exception: bool,
            session: AsyncSession,
    ):
        request = Request(scope={'type': 'http', 'headers': []})
        request.cookies['refresh_token'] = token
        jwt_service = JWTService(
            OverridenJWTRepository(
                session,
            ),
        )

        if no_exception:
            await self.save_refresh_token_to_db(session, token)

        try:
            response = await refresh_access_token(request, jwt_service)
        except HTTPException:
            if no_exception:
                assert False
            assert True
            return
        self.assert_tokens(tuple(response.values()))
        assert response.get('refresh_token') != token

        query = select(TestRefreshTokenTable)
        db_token = await session.execute(query)
        assert db_token.scalar_one().token != token

    @staticmethod
    async def save_refresh_token_to_db(session: AsyncSession, token: str):
        stmt = insert(TestRefreshTokenTable).values(user_id=1, token=token)
        await session.execute(stmt)
        await session.commit()

    async def test_count_refresh_token_if_it_was_hacked(self, session: AsyncSession):
        await self.save_refresh_token_to_db(session, 'example token')
        await self.assert_db_token_count(session, 1)

        token = generate_jwt(
            data={'sub': 1},
            lifetime_seconds=3,
            secret='JWT',
            algorithm='HS256',
        )
        request = Request(scope={'type': 'http', 'headers': []})
        request.cookies['refresh_token'] = token
        jwt_service = JWTService(
            OverridenJWTRepository(
                session,
            ),
        )

        await refresh_access_token(request, jwt_service)
        await self.assert_db_token_count(session, 1)

    @pytest.mark.parametrize(
        'token, no_exception',
        [
            ('wrong token', False),
            (None, False),
            (
                    generate_jwt(
                        data={'sub': 1},
                        lifetime_seconds=3,
                        secret='JWT',
                        algorithm='HS256',
                    ), True,
            ),
        ]
    )
    async def test_refresh_access_token(
            self,
            token: str | None,
            no_exception: bool,
            session: AsyncSession,
    ):
        request = Request(scope={'type': 'http', 'headers': []})
        request.cookies['refresh_token'] = token
        jwt_service = JWTService(
            OverridenJWTRepository(
                session,
            ),
        )

        if no_exception:
            await self.save_refresh_token_to_db(session, token)

        try:
            await logout(request, jwt_service)
        except HTTPException:
            if no_exception:
                assert False
            assert True
            return

        await self.assert_db_token_count(session, 0)
