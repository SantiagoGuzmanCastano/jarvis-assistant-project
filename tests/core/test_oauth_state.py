import pytest

from app.core.oauth_state import (
    create_oauth_state,
    validate_frontend_url,
    verify_oauth_state,
)


def test_oauth_state_preserves_allowed_frontend_origin() -> None:
    frontend_url = validate_frontend_url(
        "http://localhost:4173/",
    )

    state = create_oauth_state(
        user_id=7,
        frontend_url=frontend_url,
    )
    verified_state = verify_oauth_state(state)

    assert verified_state.user_id == 7
    assert verified_state.frontend_url == "http://localhost:4173"


def test_oauth_state_rejects_unlisted_frontend_origin() -> None:
    with pytest.raises(
        ValueError,
        match="Invalid OAuth frontend URL",
    ):
        create_oauth_state(
            user_id=7,
            frontend_url="https://attacker.example",
        )
