from fastapi import HTTPException, status
from google import genai
from google.genai import errors, types
from app.core.config import settings
from app.core.errors import AppError

def generate_gemini_response(messages,system_prompt):
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
        raise AppError(
            code="external_provider_error",
            message="Gemini could not process the request.",
            status_code=502,
        ) from error

    return response.text


def generate_gemini_intent_response(conversation_content: str,system_intent_prompt: str) -> str:
    client = genai.Client(api_key=settings.gemini_api_key)

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=conversation_content,
            config=types.GenerateContentConfig(
            system_instruction=system_intent_prompt,
            ),
)

    except errors.ServerError as error:
        raise AppError(
            code="external_provider_unavailable",
            message="Gemini is temporarily unavailable.",
            status_code=503,
        ) from error
    
    except errors.ClientError as error:
        raise AppError(
            code="external_provider_error",
            message="Gemini could not process the request.",
            status_code=502,
        ) from error

    return response.text