import pytest
from httpx import AsyncClient
from db.models.user import UserRole

pytestmark = pytest.mark.asyncio

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"


async def test_register_user(client: AsyncClient) -> None:
    """
    Test registering a new user.
    """
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "role": UserRole.USER,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == TEST_EMAIL
    assert data["data"]["role"] == UserRole.USER


async def test_register_existing_user(client: AsyncClient) -> None:
    """
    Test that registering an already registered email returns an error.
    """
    # Register first time
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "existing@example.com",
            "password": TEST_PASSWORD,
            "role": UserRole.USER,
        },
    )

    # Register second time
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "existing@example.com",
            "password": TEST_PASSWORD,
            "role": UserRole.USER,
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "already exists" in data["message"]


async def test_login_success(client: AsyncClient) -> None:
    """
    Test successful user login.
    """
    # Create the user first
    email = "login@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": TEST_PASSWORD,
            "role": UserRole.USER,
        },
    )

    # Perform login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


async def test_login_invalid_credentials(client: AsyncClient) -> None:
    """
    Test that invalid credentials return an error response.
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Incorrect email" in data["message"]


async def test_refresh_token(client: AsyncClient) -> None:
    """
    Test token rotation using a valid refresh token.
    """
    # Create and login user to acquire tokens
    email = "refresh@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": TEST_PASSWORD,
            "role": UserRole.USER,
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": TEST_PASSWORD},
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]

    # Call refresh endpoint
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
