import datetime
from typing import List
from uuid import uuid4 as uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, DateTime, UniqueConstraint, text, event
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase, AsyncAttrs):
    pass


class User(Base):
    __tablename__ = 'user'

    user_id: Mapped[uuid] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid)
    first_name: Mapped[str] = mapped_column(String(35), nullable=False)
    last_name: Mapped[str] = mapped_column(String(35), nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    post: Mapped[List['Post']] = relationship('Post', back_populates='owner', foreign_keys='Post.owner_id')
    likes_user: Mapped[List['Like']] = relationship('Like', back_populates='reviewer_ref')
    dislikes_user: Mapped[List['Dislike']] = relationship('Dislike', back_populates='reviewer_ref')

    def __repr__(self) -> str:
        return f'{self.user_id} {self.first_name} {self.last_name}'


class Post(Base):
    __tablename__ = 'post'

    post_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(60), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, default=datetime.datetime.now)
    update_at: Mapped[str] = mapped_column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    owner_id: Mapped[uuid] = mapped_column(UUID, ForeignKey(User.user_id, ondelete="CASCADE"), nullable=False)
    owner: Mapped['User'] = relationship(back_populates='post', foreign_keys='Post.owner_id')
    modify_id: Mapped[uuid] = mapped_column(UUID, ForeignKey(User.user_id, ondelete="CASCADE"), nullable=False)
    likes: Mapped[List['Like']] = relationship('Like', back_populates='post')
    dislikes: Mapped[List['Dislike']] = relationship('Dislike', back_populates='post')

    def __repr__(self) -> str:
        return f'{self.title, self.owner}'


class Rate(Base):
    __abstract__ = True

    rate_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reviewer: Mapped[str] = mapped_column(String, ForeignKey(User.email, ondelete="CASCADE"), nullable=False)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey(Post.post_id, onupdate="CASCADE"), nullable=False)
    __table_args__ = (
        UniqueConstraint('reviewer', 'post_id'),
    )


class Like(Rate):
    __tablename__ = 'like'

    post: Mapped['Post'] = relationship('Post', back_populates='likes')
    reviewer_ref: Mapped['User'] = relationship('User', back_populates='likes_user')


class Dislike(Rate):
    __tablename__ = 'dislike'

    post: Mapped['Post'] = relationship('Post', back_populates='dislikes')
    reviewer_ref: Mapped['User'] = relationship('User', back_populates='dislikes_user')
