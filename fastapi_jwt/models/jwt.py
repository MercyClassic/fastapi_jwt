from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class RefreshToken:
    __tablename__ = 'refresh_token'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(200), nullable=False)
