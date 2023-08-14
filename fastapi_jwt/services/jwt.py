from fastapi_jwt.auth.jwt import generate_jwt, decode_jwt
from fastapi_jwt.repositories.jwt.base import JWTBaseRepository


class JWTService:
    def __init__(
            self,
            jwt_repo: JWTBaseRepository,
            jwt_access_secret_key: str = 'JWT',
            jwt_refresh_secret_key: str = 'JWT',
            jwt_access_token_lifetime_seconds: int = 60 * 60 * 24 * 7,
            jwt_refresh_token_lifetime_seconds: int = 60 * 60,
            algorithm: str = 'HS256',
    ):
        self.JWT_ACCESS_SECRET_KEY = jwt_access_secret_key
        self.JWT_REFRESH_SECRET_KEY = jwt_refresh_secret_key
        self.ALGORITHM = algorithm
        self.JWT_ACCESS_TOKEN_LIFETIME_SECONDS = jwt_access_token_lifetime_seconds
        self.JWT_REFRESH_TOKEN_LIFETIME_SECONDS = jwt_refresh_token_lifetime_seconds
        self.jwt_repo = jwt_repo

    async def create_auth_tokens(self, user_id: int):
        return {
            'access_token': await self.create_access_token(user_id),
            'refresh_token': await self.create_refresh_token(user_id),
        }

    async def add_extra_info_to_access_token(self, user_id: int) -> dict:
        pass

    async def create_refresh_token(self, user_id: int) -> str:
        to_encode = {'sub': str(user_id)}
        encoded_jwt = generate_jwt(
            data=to_encode,
            lifetime_seconds=self.JWT_REFRESH_TOKEN_LIFETIME_SECONDS,
            secret=self.JWT_REFRESH_SECRET_KEY,
            algorithm=self.ALGORITHM,
        )
        await self.jwt_repo.save_refresh_token(user_id, encoded_jwt)
        return encoded_jwt

    async def create_access_token(self, user_id: int) -> str:
        to_encode = {'sub': str(user_id)}

        extra_data = await self.add_extra_info_to_access_token(user_id)
        if extra_data:
            to_encode.update(extra_data)

        return generate_jwt(
            data=to_encode,
            lifetime_seconds=self.JWT_ACCESS_TOKEN_LIFETIME_SECONDS,
            secret=self.JWT_ACCESS_SECRET_KEY,
            algorithm=self.ALGORITHM,
        )

    async def refresh_auth_tokens(self, refresh_token: str):
        refresh_token_data = decode_jwt(
            encoded_jwt=refresh_token,
            secret=self.JWT_REFRESH_SECRET_KEY,
            algorithm=self.ALGORITHM,
        )
        await self.delete_user_tokens_if_not_exist(refresh_token, refresh_token_data)

        tokens = await self.create_auth_tokens(int(refresh_token_data.get('sub')))
        return tokens

    async def delete_refresh_token(self, refresh_token: str) -> None:
        refresh_token_data = decode_jwt(
            encoded_jwt=refresh_token,
            secret=self.JWT_REFRESH_SECRET_KEY,
            algorithm=self.ALGORITHM,
            soft=True,
        )
        await self.delete_user_tokens_if_not_exist(refresh_token, refresh_token_data)

    async def delete_user_tokens_if_not_exist(self, token: str, token_data: dict) -> None:
        deleted_id = await self.jwt_repo.delete_refresh_token(token)
        """
        DELETE TOKEN AND RETURNING ID
        IF ID IS NONE THAT MEANS ID WAS DELETED EARLY, MOST LIKELY BY HACKER
        """
        if not deleted_id:
            await self.jwt_repo.delete_all_user_refresh_tokens(int(token_data.get('sub')))
