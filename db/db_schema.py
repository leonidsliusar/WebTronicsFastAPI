from uuid import uuid4 as uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, DateTime, UniqueConstraint
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
    post: Mapped[list['Post']] = relationship(back_populates='owner', foreign_keys='Post.owner_id')
    likes: Mapped[list['Like']] = relationship(back_populates='reviewer_like_rate')
    dislikes: Mapped[list['Dislike']] = relationship(back_populates='reviewer_dis_rate')

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
    owner: Mapped['User'] = relationship(back_populates='post', foreign_keys='Post.owner_id')
    modify_id: Mapped[uuid] = mapped_column(UUID, ForeignKey(User.user_id, ondelete="CASCADE"), nullable=False)
    like_rate: Mapped[list['Like']] = relationship(back_populates='post_like_rate')
    dis_rate: Mapped[list['Dislike']] = relationship(back_populates='post_dis_rate')

    def __init__(self) -> None:
        super().__init__()
        self.modify_id = self.owner_id

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

    post_like_rate: Mapped[list['Post']] = relationship(back_populates='like_rate')
    reviewer_like_rate: Mapped[list['User']] = relationship(back_populates='likes')


class Dislike(Rate):
    __tablename__ = 'dislike'

    post_dis_rate: Mapped[list['Post']] = relationship(back_populates='dis_rate')
    reviewer_dis_rate: Mapped[list['User']] = relationship(back_populates='dislikes')
