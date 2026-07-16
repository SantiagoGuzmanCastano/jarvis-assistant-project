

import asyncio
import json
from unittest.mock import Mock

from app.core.errors import AppError
from app.core.exception_handlers import app_error_handler


def test_app_error_handler_returns_standard_error_response() -> None:
    exc = AppError(
        code="http_error",
        message="The request could not be completed.",
        status_code=500,
        details={},
    )

    response = asyncio.run(
        app_error_handler(request=Mock(), exc=exc,))
    
    assert response.status_code == 500
    assert json.loads(response.body) == {
        "error": {
            "code": "http_error",
            "message": "The request could not be completed.",
            "details": {},
        }
    }