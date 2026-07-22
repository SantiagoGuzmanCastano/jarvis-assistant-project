from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.core.errors import AppError
from app.db.session import get_session
from app.main import app
from app.routers import auth as auth_router


def test_refresh_endpoint_returns_rotated_tokens() -> None:
    database_session = Mock()

    def override_get_session():
        yield database_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        with (
            TestClient(app) as client,
            patch.object(
                auth_router,
                "refresh_user_session",
                return_value={
                    "access_token": "new-access-token",
                    "refresh_token": "new-refresh-token",
                    "token_type": "bearer",
                },
            ) as refresh_service,
        ):
            response = client.post(
                "/auth/refresh",
                json={"refresh_token": "current-refresh-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token",
        "token_type": "bearer",
    }
    refresh_service.assert_called_once_with(
        refresh_token="current-refresh-token",
        session=database_session,
    )


def test_refresh_endpoint_returns_the_service_error_contract() -> None:
    database_session = Mock()

    def override_get_session():
        yield database_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        with (
            TestClient(app) as client,
            patch.object(
                auth_router,
                "refresh_user_session",
                side_effect=AppError(
                    code="invalid_refresh_token",
                    message="The refresh token is invalid or expired.",
                    status_code=401,
                ),
            ),
        ):
            response = client.post(
                "/auth/refresh",
                json={"refresh_token": "invalid-refresh-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "invalid_refresh_token",
            "message": "The refresh token is invalid or expired.",
            "details": {},
        }
    }


def test_refresh_endpoint_rejects_a_missing_refresh_token() -> None:
    with TestClient(app) as client:
        response = client.post("/auth/refresh", json={})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_logout_endpoint_revokes_the_supplied_refresh_token() -> None:
    database_session = Mock()

    def override_get_session():
        yield database_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        with (
            TestClient(app) as client,
            patch.object(auth_router, "log_user_out") as logout_service,
        ):
            response = client.post(
                "/auth/logout",
                json={"refresh_token": "current-refresh-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""
    logout_service.assert_called_once_with(
        refresh_token="current-refresh-token",
        session=database_session,
    )


def test_logout_endpoint_rejects_a_missing_refresh_token() -> None:
    with TestClient(app) as client:
        response = client.post("/auth/logout", json={})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
