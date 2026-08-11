

from unittest.mock import Mock, patch

import pytest
from google.genai import errors

from app.core.errors import AppError
from app.integrations.gemini_client import (
    generate_gemini_intent_response,
    generate_gemini_response,
    generate_gemini_structured_response,
)
from app.services.calendar_event_extraction import ExtractedCalendarEvent


# Mientras este test corre,
# cuando gemini_client.py use genai.Client,
# no uses el constructor real.
# Usa un objeto falso.
@patch("app.integrations.gemini_client.genai.Client")
def test_server_error_becomes_provider_unavailable(client_mock: Mock):

    #client mock, representa a genai.client
    client = client_mock.return_value
    client.models.generate_content.side_effect = errors.ServerError(503, {"error":{"message":"Unavailable"}})

    with pytest.raises(AppError) as error_info:
        generate_gemini_response(
            messages=[],
            system_prompt="You are Jarvis.",
        )

    error = error_info.value

    assert error.code == "external_provider_unavailable"
    assert error.status_code == 503

@patch("app.integrations.gemini_client.genai.Client")
def test_client_error_becomes_provider_error(client_mock: Mock):

    #client mock, representa a genai.client
    client = client_mock.return_value
    client.models.generate_content.side_effect = errors.ClientError(400, {"error": {"message": "Invalid provider request"}},)

    with pytest.raises(AppError) as error_info:
        generate_gemini_response(
            messages=[],
            system_prompt="You are Jarvis.",
        )

    error = error_info.value

    assert error.code == "external_provider_error"
    assert error.status_code == 502


@patch("app.integrations.gemini_client.genai.Client")
def test_empty_response_becomes_provider_error(client_mock: Mock):
    client = client_mock.return_value
    client.models.generate_content.return_value = Mock(text=None)

    with pytest.raises(AppError) as error_info:
        generate_gemini_response(
            messages=[],
            system_prompt="You are Jarvis.",
        )

    error = error_info.value

    assert error.code == "external_provider_invalid_response"
    assert error.status_code == 502



@patch("app.integrations.gemini_client.genai.Client")
def test_intent_response_server_error_becomes_provider_unavailable(client_mock: Mock):

    #client mock, representa a genai.client
    client = client_mock.return_value
    client.models.generate_content.side_effect = errors.ServerError(503, {"error":{"message":"Unavailable"}})

    with pytest.raises(AppError) as error_info:
        generate_gemini_intent_response(
            conversation_content="Read my latest emails.",
            system_intent_prompt="Classify the user's intent and return JSON."
        )

    error = error_info.value

    assert error.code == "external_provider_unavailable"
    assert error.status_code == 503



@patch("app.integrations.gemini_client.genai.Client")
def test_intent_response_client_error_becomes_provider_error(client_mock: Mock):

    #client mock, representa a genai.client
    client = client_mock.return_value
    client.models.generate_content.side_effect = errors.ClientError(400, {"error": {"message": "Invalid provider request"}},)

    with pytest.raises(AppError) as error_info:
        generate_gemini_intent_response(
            conversation_content="Read my latest emails.",
            system_intent_prompt="Classify the user's intent and return JSON."
        )

    error = error_info.value

    assert error.code == "external_provider_error"
    assert error.status_code == 502


@patch("app.integrations.gemini_client.genai.Client")
def test_empty_intent_response_becomes_provider_error(client_mock: Mock):
    client = client_mock.return_value
    client.models.generate_content.return_value = Mock(text="   ")

    with pytest.raises(AppError) as error_info:
        generate_gemini_intent_response(
            conversation_content="Read my latest emails.",
            system_intent_prompt="Classify the user's intent and return JSON.",
        )

    error = error_info.value

    assert error.code == "external_provider_invalid_response"
    assert error.status_code == 502


@patch("app.integrations.gemini_client.genai.Client")
def test_intent_response_requests_json(client_mock: Mock):
    client = client_mock.return_value
    client.models.generate_content.return_value = Mock(
        text='{"needs_tool":false,"tool_name":null,"arguments":{}}'
    )

    generate_gemini_intent_response(
        conversation_content="Hello.",
        system_intent_prompt="Classify the intent.",
    )

    config = client.models.generate_content.call_args.kwargs["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_schema is None


@patch("app.integrations.gemini_client.genai.Client")
def test_intent_rate_limit_becomes_provider_unavailable(client_mock: Mock):
    client = client_mock.return_value
    client.models.generate_content.side_effect = errors.ClientError(
        429,
        {"error": {"message": "Rate limit exceeded"}},
    )

    with pytest.raises(AppError) as error_info:
        generate_gemini_intent_response(
            conversation_content="Read my latest emails.",
            system_intent_prompt="Classify the intent.",
        )

    assert error_info.value.code == "external_provider_unavailable"
    assert error_info.value.status_code == 503


@patch("app.integrations.gemini_client.genai.Client")
def test_intent_sdk_value_error_becomes_configuration_error(
    client_mock: Mock,
):
    client = client_mock.return_value
    client.models.generate_content.side_effect = ValueError(
        "Unsupported response schema"
    )

    with pytest.raises(AppError) as error_info:
        generate_gemini_intent_response(
            conversation_content="Read my latest emails.",
            system_intent_prompt="Classify the intent.",
        )

    assert (
        error_info.value.code
        == "external_provider_configuration_error"
    )
    assert error_info.value.status_code == 500


@patch("app.integrations.gemini_client.genai.Client")
def test_structured_response_uses_json_schema_field(client_mock: Mock):
    client = client_mock.return_value
    client.models.generate_content.return_value = Mock(
        text=(
            '{"title":"Reunión","description":null,'
            '"start_date":"2026-08-04T19:00:00-05:00",'
            '"end_date":"2026-08-04T20:00:00-05:00",'
            '"location":null}'
        )
    )

    result = generate_gemini_structured_response(
        content="Extract the event.",
        system_prompt="Return JSON.",
        response_schema=ExtractedCalendarEvent,
    )

    config = client.models.generate_content.call_args.kwargs["config"]
    assert config.response_schema is None
    assert config.response_json_schema["additionalProperties"] is False
    assert result.title == "Reunión"
