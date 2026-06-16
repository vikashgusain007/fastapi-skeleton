import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from core.dependencies import get_db, get_redis
from db.base import Base
from main import app
from unittest.mock import AsyncMock

# Use in-memory SQLite for self-contained and fast test executions
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Ensure a session-scoped event loop is used.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Create database tables on test session startup.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide transactional database sessions, rolling back changes after each test.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()

    session_maker = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    session = session_maker()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def mock_redis():
    """
    Provide an AsyncMock representing Redis to avoid calling local Redis.
    """
    mock = AsyncMock()
    mock.ping.return_value = True

    # Setup pipeline mock for sliding window rate limiter
    pipeline_mock = AsyncMock()
    pipeline_mock.execute.return_value = (None, 1, None, None)
    mock.pipeline.return_value.__aenter__.return_value = pipeline_mock

    return mock


@pytest_asyncio.fixture
async def client(db_session, mock_redis) -> AsyncGenerator[AsyncClient, None]:
    """
    Set up FastAPI testing client with database and Redis overrides.
    """
    async def override_db():
        yield db_session

    async def override_redis():
        yield mock_redis

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
