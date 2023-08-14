from starlette.requests import Request

from fastapi_jwt.schemas.jwt import AuthenticateSchema
from fastapi_jwt.services.jwt import JWTService
from fastapi_jwt.services.users import UserService


async def login(
        authenticate_data: AuthenticateSchema,
        jwt_service: JWTService,
        user_service: UserService,
) -> dict:
    user_id = await user_service.authenticate(**authenticate_data.model_dump())
    tokens = await jwt_service.create_auth_tokens(user_id)
    return tokens


async def refresh_access_token(
        request: Request,
        jwt_service: JWTService,
) -> dict:
    tokens = await jwt_service.refresh_auth_tokens(request.cookies.get('refresh_token'))
    return tokens


async def logout(
        request: Request,
        jwt_service: JWTService,
) -> None:
    await jwt_service.delete_refresh_token(request.cookies.get('refresh_token'))
