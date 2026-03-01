from typing import Annotated, Optional
from sqlalchemy import BigInteger, String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base, BigInt, AutoDateTime, IntPK, Str, TextStr

class CommonMistake(Base):
    __tablename__ = "common_mistakes"

    id: Mapped[IntPK]
    language: Mapped[Str]
    pattern: Mapped[Optional[Str]]
    exit_code: Mapped[Optional[int]]
    hint: Mapped[TextStr]
    category: Mapped[Str]
    date_created: Mapped[AutoDateTime]
    last_updated: Mapped[AutoDateTime]
