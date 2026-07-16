
from app.core.config import settings

import requests

from app.core.errors import AppError



def request_gmail(method: str, url: str, params: dict | None = None, json:dict |None = None, data: dict | None = None, headers: dict | None = None, ) -> requests.Response:

    #request.Response es la respuesta del method solicitado

    try:
        response = requests.request(
        method=method,
        url=url,
        data=data,
        headers=headers,
        params=params,
        json=json,
        timeout=settings.google_request_timeout_seconds,
        )
        response.raise_for_status()
        return response
    
    except requests.Timeout as error:
        raise AppError(
            code="external_provider_unavailable",
            message="Gmail is temporarily unavailable",
            status_code=503,
        ) from error
    
        
    except requests.HTTPError as error:
        if error.response is not None:
            provider_status = error.response.status_code
        else:
            provider_status = 502

        if provider_status == 401:
            raise AppError(
                code="external_provider_authentication_failed",
                message="Gmail authentication failed.",
                status_code=401
            ) from error

        if provider_status == 403:
            raise AppError(
                code="external_provider_forbidden",
                message="Gmail access is forbidden.",
                status_code=403,
            ) from error

        if provider_status == 404:
            raise AppError(
                code="external_provider_not_found",
                message="The requested Gmail resource was not found.",
                status_code=404,
            ) from error

        if provider_status == 429:
            raise AppError(
                code="external_provider_rate_limited",
                message="Gmail rate limit was reached.",
                status_code=429,
            ) from error

        if provider_status >= 500:
            raise AppError(
                code="external_provider_unavailable",
                message="Gmail is temporarily unavailable.",
                status_code=503,
            ) from error

        raise AppError(
            code="external_provider_error",
            message="Gmail could not process the request.",
            status_code=502,
        ) from error



    except requests.RequestException  as error:
        raise AppError(
            code="external_provider_unavailable",
            message="Gmail is temporarily unavailable",
            status_code=503,
        ) from error
