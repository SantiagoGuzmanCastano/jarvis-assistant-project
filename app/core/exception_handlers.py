
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from app.core.errors import AppError

from fastapi.responses import JSONResponse


async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "The request data is invalid.",
                "details": {
                    "fields": [
                    {
                        "loc": error["loc"],
                        "msg": error["msg"],
                        "type": error["type"],
                    }
                    for error in exc.errors()
                ],
                },
            },
        },
    )

async def authentication_error_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={
            "error": {
                "code": "authentication_error",
                "message": "Authentication is required or the token is invalid.",
                "details": {},
            },
        },
    )

async def authorization_error_handler(request, exc):
    return JSONResponse(
        status_code=403,
        content={
            "error": {
                "code": "authorization_error",
                "message": "You do not have permission to perform this action.",
                "details": {},
            },
        },
    )

# Recibe cualquier HTTPException.
# Si es 401, usa el error de autenticación.
# Si es 403, usa el error de autorización.
# Si es otro código, usa el error 
# esto es una forma de comunicar el fallo al front
async def http_exception_handler(request, exc: HTTPException):
    if exc.status_code == 401:
        return await authentication_error_handler(request, exc)

    if exc.status_code == 403:
        return await authorization_error_handler(request, exc)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "http_error",
                "message": "The request could not be completed.",
                "details": {},
            },
        },
    )


#esto sirve para que el front siempre reciba los errores con la misma forma
async def app_error_handler(request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )