from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from app.core.errors import AppError

from app.core.exception_handlers import (
    app_error_handler,
    http_exception_handler,
    validation_exception_handler,
)

#Voy a tomar todos los endpoints de este archivo
from app.db.init_db import create_db_tables
from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.conversation import router as conversation_router
from app.routers.chat import router as chat_router
from app.routers.user_settings import router as user_settings_router
from app.routers.external_auth import router as external_auth_router





#lifespan es la logica de inicio y de cierre de la app
#cuando arranca la app -> crear tablas si no existen
#cuando se apaga la app -> no hacemos nada por ahora
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_tables()
    yield
    
app = FastAPI(title=settings.app_name, lifespan=lifespan)

#middleware es el codigo que se ejecuta alrededor de cada solicitud HTTP, antes de que llegue a un router y antes de que vuelva la respuesta
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)
app.add_exception_handler(
    HTTPException,
    http_exception_handler,
)

app.add_exception_handler(AppError, app_error_handler)


#Voy a tomar todos los endpoints de este archivo
#Y los voy a agregar a la app principal
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(conversation_router)
app.include_router(chat_router)
app.include_router(user_settings_router)
app.include_router(external_auth_router)




