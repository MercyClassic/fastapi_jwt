from fastapi import HTTPException
from starlette import status

from fastapi_jwt.managers.users import UserManager
from fastapi_jwt.repositories.users import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def authenticate(
            self,
            username_field: str,
            input_password: str,
            **kwargs,
    ) -> int:
        user = await self.user_repo.get_info_for_authenticate(username_field)
        if not user or not UserManager.check_password(
                input_password=input_password,
                password_from_db=user.password,
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail='Credentials are not valid',
            )
        if 'is_active' in dir(user) and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Account is not active',
            )
        return user.id
