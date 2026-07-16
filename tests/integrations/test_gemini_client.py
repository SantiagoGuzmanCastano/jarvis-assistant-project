

from unittest.mock import Mock, patch

import pytest
from google.genai import errors

from app.core.errors import AppError
from app.integrations.gemini_client import generate_gemini_intent_response, generate_gemini_response


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