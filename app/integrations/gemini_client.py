import logging

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.errors import AppError


logger = logging.getLogger(__name__)


def _raise_gemini_client_error(error: errors.ClientError) -> None:
    logger.error(
        "Gemini rejected the request: code=%s status=%s message=%s",
        error.code,
        error.status,
        error.message,
    )

    if error.code == 429:
        raise AppError(
            code="external_provider_unavailable",
            message="Gemini is temporarily unavailable.",
            status_code=503,
        ) from error

    raise AppError(
        code="external_provider_error",
        message="Gemini could not process the request.",
        status_code=502,
    ) from error


def _raise_gemini_configuration_error(error: ValueError) -> None:
    logger.exception("Gemini request configuration is invalid.")
    raise AppError(
        code="external_provider_configuration_error",
        message="Gemini request configuration is invalid.",
        status_code=500,
    ) from error


def _get_gemini_response_text(response) -> str:
    try:
        response_text = response.text
    except (AttributeError, ValueError) as error:
        raise AppError(
            code="external_provider_invalid_response",
            message="Gemini returned an empty response.",
            status_code=502,
        ) from error

    if not isinstance(response_text, str) or not response_text.strip():
        raise AppError(
            code="external_provider_invalid_response",
            message="Gemini returned an empty response.",
            status_code=502,
        )

    return response_text


def generate_gemini_response(messages, system_prompt):
    client = genai.Client(api_key=settings.gemini_api_key)

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
    except errors.ServerError as error:
        raise AppError(
            code="external_provider_unavailable",
            message="Gemini is temporarily unavailable.",
            status_code=503,
        ) from error
    except errors.ClientError as error:
        _raise_gemini_client_error(error)
    except ValueError as error:
        _raise_gemini_configuration_error(error)

    return _get_gemini_response_text(response)


def generate_gemini_intent_response(
    conversation_content: str,
    system_intent_prompt: str,
) -> str:
    client = genai.Client(api_key=settings.gemini_api_key)

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=conversation_content,
            config=types.GenerateContentConfig(
                system_instruction=system_intent_prompt,
                response_mime_type="application/json",
            ),
        )
    except errors.ServerError as error:
        raise AppError(
            code="external_provider_unavailable",
            message="Gemini is temporarily unavailable.",
            status_code=503,
        ) from error
    except errors.ClientError as error:
        _raise_gemini_client_error(error)
    except ValueError as error:
        _raise_gemini_configuration_error(error)

    return _get_gemini_response_text(response)


def generate_gemini_structured_response(
    *,
    content: str,
    system_prompt: str,
    response_schema: type[BaseModel],
) -> BaseModel:
    client = genai.Client(api_key=settings.gemini_api_key)

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_json_schema=(
                    response_schema.model_json_schema()
                ),
            ),
        )
    except errors.ServerError as error:
        raise AppError(
            code="external_provider_unavailable",
            message="Gemini is temporarily unavailable.",
            status_code=503,
        ) from error
    except errors.ClientError as error:
        _raise_gemini_client_error(error)
    except ValueError as error:
        _raise_gemini_configuration_error(error)

    try:
        return response_schema.model_validate_json(
            _get_gemini_response_text(response)
        )
    except ValidationError as error:
        raise AppError(
            code="external_provider_invalid_response",
            message="Gemini returned invalid structured data.",
            status_code=502,
        ) from error
