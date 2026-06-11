from fastapi import HTTPException, status
from google import genai
from google.genai import errors
from app.core.config import settings


def generate_gemini_response(messages):
    client = genai.Client(api_key=settings.gemini_api_key)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=messages,
        )

    except errors.ServerError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini is temporarily unavailable. Try again later.",
        )

    return response.text