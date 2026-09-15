import uuid
from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import settings


def now():
    return datetime.now(timezone.utc)


def uid():
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class ChatSession(Base):
    __tablename__ = 'sessions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    owner: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(120), default='Untitled conversation')
    user_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    session_id: Mapped[str] = mapped_column(ForeignKey('sessions.id', ondelete='CASCADE'), index=True)
    role: Mapped[str] = mapped_column(String(12))
    content: Mapped[str] = mapped_column(Text)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Artifact(Base):
    __tablename__ = 'artifacts'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    session_id: Mapped[str] = mapped_column(ForeignKey('sessions.id', ondelete='CASCADE'), index=True)
    message_id: Mapped[str] = mapped_column(ForeignKey('messages.id', ondelete='CASCADE'))
    title: Mapped[str] = mapped_column(String(160))
    format: Mapped[str] = mapped_column(String(12))
    content: Mapped[str] = mapped_column(Text)
    sources: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Transcript(Base):
    __tablename__ = 'transcripts'
    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    guest: Mapped[str] = mapped_column(String(250))
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    youtube_url: Mapped[str] = mapped_column(Text, default='')
    content_hash: Mapped[str] = mapped_column(String(64))
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Chunk(Base):
    __tablename__ = 'chunks'
    __table_args__ = (UniqueConstraint('transcript_id', 'position'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    transcript_id: Mapped[str] = mapped_column(ForeignKey('transcripts.id', ondelete='CASCADE'), index=True)
    position: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[str] = mapped_column(String(20), default='')


cfg = settings()
if cfg.database_url.startswith('sqlite') and not cfg.allow_sqlite:
    raise RuntimeError('PostgreSQL is required. ALLOW_SQLITE is reserved for tests.')
engine = create_engine(cfg.database_url, pool_pre_ping=True, **(
    {'connect_args': {'check_same_thread': False}} if cfg.database_url.startswith('sqlite') else
    {'connect_args': {'connect_timeout': 5}}
))
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        yield db
