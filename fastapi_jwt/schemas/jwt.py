from pydantic import BaseModel


class AuthenticateSchema(BaseModel):
    username_field: str
    input_password: str
