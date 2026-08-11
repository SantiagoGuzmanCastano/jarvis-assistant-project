import requests

from app.core.config import settings
from app.core.errors import AppError


def request_calendar(
    method: str,
    url: str,
    params: dict | None = None,
    json: dict | None = None,
    headers: dict | None = None,
) -> requests.Response:
    try:
        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=json,
            headers=headers,
            timeout=settings.google_request_timeout_seconds,
        )
        response.raise_for_status()
        return response
    except requests.Timeout as error:
        raise AppError(
            code="external_provider_unavailable",
            message="Google Calendar is temporarily unavailable.",
            status_code=503,
        ) from error
    except requests.HTTPError as error:
        provider_status = (
            error.response.status_code
            if error.response is not None
            else 502
        )

        if provider_status == 401:
            raise AppError(
                code="external_provider_authentication_failed",
                message="Google Calendar authentication failed.",
                status_code=401,
            ) from error

        if provider_status == 403:
            raise AppError(
                code="external_provider_forbidden",
                message="Google Calendar access is forbidden.",
                status_code=403,
            ) from error

        if provider_status == 404:
            raise AppError(
                code="external_provider_not_found",
                message="The requested Google Calendar resource was not found.",
                status_code=404,
            ) from error

        if provider_status == 429:
            raise AppError(
                code="external_provider_rate_limited",
                message="Google Calendar rate limit was reached.",
                status_code=429,
            ) from error

        if provider_status >= 500:
            raise AppError(
                code="external_provider_unavailable",
                message="Google Calendar is temporarily unavailable.",
                status_code=503,
            ) from error

        raise AppError(
            code="external_provider_error",
            message="Google Calendar could not process the request.",
            status_code=502,
        ) from error
    except requests.RequestException as error:
        raise AppError(
            code="external_provider_unavailable",
            message="Google Calendar is temporarily unavailable.",
            status_code=503,
        ) from error
