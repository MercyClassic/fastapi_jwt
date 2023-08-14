from starlette.requests import Request


async def get_access_token_from_headers(request: Request) -> str:
    return request.headers.get('Authorization')
