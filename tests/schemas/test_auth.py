import pytest
from pydantic import ValidationError

from app.schemas.auth import UserLogin, UserRegister


@pytest.mark.parametrize("schema", [UserRegister, UserLogin])
def test_auth_password_accepts_the_shared_maximum_length(schema: type) -> None:
    payload = schema(
        email="lina@example.com",
        password="a" * 25,
    )

    assert payload.password == "a" * 25


@pytest.mark.parametrize("schema", [UserRegister, UserLogin])
def test_auth_password_rejects_values_above_the_shared_maximum_length(
    schema: type,
) -> None:
    with pytest.raises(ValidationError):
        schema(
            email="lina@example.com",
            password="a" * 26,
        )
