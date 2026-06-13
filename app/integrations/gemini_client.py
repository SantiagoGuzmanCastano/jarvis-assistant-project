from fastapi import HTTPException, status
from google import genai
from google.genai import errors, types
from app.core.config import settings


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

    except errors.ServerError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini is temporarily unavailable. Try again later.",
        )
    
    except errors.ClientError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    return response.text