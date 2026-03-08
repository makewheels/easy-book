"""
pytest configuration for easy-book backend tests
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from api_server.main import app
from api_server.database import connect_to_mongo, close_mongo_connection, get_database


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client():
    """Create an async HTTP test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Connect to MongoDB before tests, disconnect after."""
    await connect_to_mongo()
    yield
    await close_mongo_connection()


@pytest_asyncio.fixture
async def clean_db():
    """Clean all test data from MongoDB collections."""
    db = get_database()
    yield db
    # Cleanup after test
    await db.db.students.delete_many({})
    await db.db.appointments.delete_many({})
    await db.db.courses.delete_many({})
    await db.db.packages.delete_many({})
    await db.db.attendances.delete_many({})
