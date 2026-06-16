import pytest
from httpx import AsyncClient
from db.models.user import UserRole

pytestmark = pytest.mark.asyncio


async def test_get_me_unauthorized(client: AsyncClient) -> None:
    """
    Verify that GET /users/me fails if no authorization header is sent.
    """
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


async def test_get_me_success(client: AsyncClient) -> None:
    """
    Verify that a logged-in user can retrieve their profile details.
    """
    # Create and login user
    email = "me@example.com"
    password = "password123"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": UserRole.USER},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_resp.json()["data"]["access_token"]

    # Request profile
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == email
    assert data["data"]["role"] == UserRole.USER


async def test_rbac_admin_only_forbidden(client: AsyncClient) -> None:
    """
    Verify that a standard user role cannot access the admin-only endpoint.
    """
    # Create and login standard user
    email = "user@example.com"
    password = "password123"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": UserRole.USER},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_resp.json()["data"]["access_token"]

    # Request admin-only endpoint
    response = await client.get(
        "/api/v1/users/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert "permission" in data["message"].lower()


async def test_rbac_admin_only_success(client: AsyncClient) -> None:
    """
    Verify that an admin user can access the admin-only endpoint.
    """
    # Create and login admin user
    email = "admin@example.com"
    password = "password123"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": UserRole.ADMIN},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_resp.json()["data"]["access_token"]

    # Request admin-only endpoint
    response = await client.get(
        "/api/v1/users/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == email
    assert data["data"]["role"] == UserRole.ADMIN
