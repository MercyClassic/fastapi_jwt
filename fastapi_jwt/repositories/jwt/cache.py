from redis.client import Redis

from fastapi_jwt.repositories.jwt.base import JWTBaseRepository


class JWTRepository(JWTBaseRepository):

    def __init__(self, redis: Redis):
        self.redis = redis

    async def save_refresh_token(self, user_id: int, token: str) -> None:
        self.redis.set(f'{user_id},{token}', 1)

    async def delete_refresh_token(self, token: str) -> int | None:
        key = self.redis.keys(f'*,{token}*')
        if len(key) == 0:
            return
        self.redis.delete(key[0])
        return int(key[0].decode('utf-8').split(',')[0])

    async def delete_all_user_refresh_tokens(self, user_id: int) -> None:
        user_tokens = self.redis.keys(f'*{user_id},*')
        for token in user_tokens:
            self.redis.delete(token)
