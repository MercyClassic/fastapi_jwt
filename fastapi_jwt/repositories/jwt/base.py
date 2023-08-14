

class JWTBaseRepository:

    async def save_refresh_token(self, user_id: int, token: str) -> None:
        raise NotImplementedError

    async def delete_refresh_token(self, token: str) -> int | None:
        raise NotImplementedError

    async def delete_all_user_refresh_tokens(self, user_id) -> None:
        raise NotImplementedError
