from uuid import uuid4 as uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'user'

    user_id: Mapped[uuid] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid)
    first_name: Mapped[str] = mapped_column(String(35), nullable=False)
    last_name: Mapped[str] = mapped_column(String(35), nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    post: Mapped[list['Post']] = relationship(back_populates='owner')

    def __repr__(self) -> str:
        return f'{self.user_id} {self.first_name} {self.last_name}'


class Post(Base):
    __tablename__ = 'user_post'

    post_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(60), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, default=now)
    update_at: Mapped[str] = mapped_column(DateTime, default=now, onupdate=now)
    owner_id: Mapped[uuid] = mapped_column(UUID, ForeignKey(User.user_id, ondelete="CASCADE"), nullable=False)
    owner: Mapped['User'] = relationship(back_populates='post')

    def __repr__(self) -> str:
        return f'{self.title, self.owner}'


class Rating(Base):
    __tablename__ = 'raitng'

    rate_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
