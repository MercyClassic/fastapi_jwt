import pytest
from fastapi import HTTPException
from redis.client import Redis
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from fastapi_jwt.auth.jwt import decode_jwt, generate_jwt
from fastapi_jwt.exceptions.jwt import FailGetAttribute
from fastapi_jwt.managers.users import UserManager
from fastapi_jwt.schemas.jwt import AuthenticateSchema
from fastapi_jwt.repositories.jwt.cache import JWTRepository
from fastapi_jwt.repositories.users import UserRepository
from fastapi_jwt.services.jwt import JWTService
from fastapi_jwt.services.users import UserService
from tests.conftest import (
    TestAccountTable,
)
from fastapi_jwt.actions.jwt import login, refresh_access_token, logout


redis = Redis()


class OverridenUserRepository(UserRepository):
    model = TestAccountTable


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
        keys = redis.keys('*')
        for key in keys:
            redis.delete(key)

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
            JWTRepository(
                redis,
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

            await self.assert_db_token_count(result_count)

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
    async def assert_db_token_count(result_count: int) -> None:
        keys = redis.keys('*')
        assert len(keys) == result_count

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
    ):
        request = Request(scope={'type': 'http', 'headers': []})
        request.cookies['refresh_token'] = token
        jwt_service = JWTService(
            JWTRepository(
                redis,
            ),
        )

        if no_exception:
            await self.save_refresh_token_to_db(token)

        try:
            response = await refresh_access_token(request, jwt_service)
        except HTTPException:
            if no_exception:
                assert False
            assert True
            return
        self.assert_tokens(tuple(response.values()))
        assert response.get('refresh_token') != token

        keys = redis.keys('*')
        assert keys[0].decode('utf-8').split(',')[0] != token

    @staticmethod
    async def save_refresh_token_to_db(token: str):
        redis.set(f'1,{token}', 1)

    async def test_count_refresh_token_if_it_was_hacked(self):
        await self.save_refresh_token_to_db('example token')
        await self.assert_db_token_count(1)

        token = generate_jwt(
            data={'sub': 1},
            lifetime_seconds=3,
            secret='JWT',
            algorithm='HS256',
        )
        request = Request(scope={'type': 'http', 'headers': []})
        request.cookies['refresh_token'] = token
        jwt_service = JWTService(
            JWTRepository(
                redis,
            ),
        )

        await refresh_access_token(request, jwt_service)
        await self.assert_db_token_count(1)

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
    ):
        request = Request(scope={'type': 'http', 'headers': []})
        request.cookies['refresh_token'] = token
        jwt_service = JWTService(
            JWTRepository(
                redis,
            ),
        )

        if no_exception:
            await self.save_refresh_token_to_db(token)

        try:
            await logout(request, jwt_service)
        except HTTPException:
            if no_exception:
                assert False
            assert True
            return

        await self.assert_db_token_count(0)
