import pytest
from app.models.enums import UserRole


def test_valid_login_worker(client):
    """
    Test logging in with valid worker credentials returns JWT and user profile.
    """
    response = client.post(
        "/api/auth/login",
        json={
            "email": "worker@safetyintelligence.internal",
            "password": "Worker@2026",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "worker@safetyintelligence.internal"
    assert data["user"]["role"] == "WORKER"
    # Verify password_hash is not returned
    assert "password_hash" not in data["user"]
    assert "password" not in data["user"]


def test_valid_login_admin(client):
    """
    Test valid credentials for admin.
    """
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@safetyintelligence.internal",
            "password": "Admin@2026",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "ADMIN"
    assert "password_hash" not in data["user"]


def test_invalid_login_wrong_password(client):
    """
    Test login fails with 401 when password is incorrect.
    """
    response = client.post(
        "/api/auth/login",
        json={
            "email": "worker@safetyintelligence.internal",
            "password": "WrongPassword123!",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data or "detail" in data


def test_invalid_login_nonexistent_user(client):
    """
    Test login fails with 401 for unknown email.
    """
    response = client.post(
        "/api/auth/login",
        json={
            "email": "ghost.user@nonexistent.internal",
            "password": "SomePassword123!",
        },
    )
    assert response.status_code == 401


def test_user_registration(client):
    """
    Test registering a new user returns 201 with user profile and no password hash.
    """
    response = client.post(
        "/api/auth/register",
        json={
            "name": "New Safety Specialist",
            "email": "new.specialist@safetyintelligence.internal",
            "password": "SecurePassword@2026",
            "role": "ADMIN",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new.specialist@safetyintelligence.internal"
    assert data["role"] == "ADMIN"
    assert "password_hash" not in data
    assert "password" not in data


def test_user_registration_duplicate_email(client):
    """
    Test duplicate email registration returns 400.
    """
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Duplicate Worker",
            "email": "worker@safetyintelligence.internal",
            "password": "AnotherPassword@2026",
            "role": "WORKER",
        },
    )
    assert response.status_code == 400


def test_get_me_authenticated(client):
    """
    Test GET /api/auth/me with valid Bearer token returns current user profile.
    """
    # 1. Login
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "admin@safetyintelligence.internal",
            "password": "Admin@2026",
        },
    )
    token = login_res.json()["access_token"]

    # 2. Query /me
    me_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["email"] == "admin@safetyintelligence.internal"
    assert user_data["role"] == "ADMIN"
    assert "password_hash" not in user_data


def test_get_me_unauthenticated(client):
    """
    Test GET /api/auth/me without token returns 401 Unauthorized.
    """
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_get_me_invalid_token(client):
    """
    Test GET /api/auth/me with bogus token returns 401.
    """
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.string"},
    )
    assert response.status_code == 401


# ==============================================================================
# RBAC Backend Authorization Tests (Isolated from frontend)
# ==============================================================================

def _get_token_for(client, email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_worker_rbac_permissions(client):
    """
    Worker:
    - Access worker endpoint: Allowed (200)
    - Access admin endpoint: Forbidden (403)
    """
    token = _get_token_for(client, "worker@safetyintelligence.internal", "Worker@2026")
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/auth/rbac/worker", headers=headers).status_code == 200
    assert client.get("/api/auth/rbac/admin", headers=headers).status_code == 403


def test_admin_rbac_permissions(client):
    """
    Admin:
    - Access all endpoints: Allowed (200)
    """
    token = _get_token_for(client, "admin@safetyintelligence.internal", "Admin@2026")
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/auth/rbac/worker", headers=headers).status_code == 200
    assert client.get("/api/auth/rbac/admin", headers=headers).status_code == 200
