from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.core.config import settings

#Voy a tomar todos los endpoints de este archivo
from app.db.init_db import create_db_tables
from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.conversation import router as conversation_router



#lifespan es la logica de inicio y de cierre de la app
#cuando arranca la app -> crear tablas si no existen
#cuando se apaga la app -> no hacemos nada por ahora
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_tables()
    yield
    
app = FastAPI(title=settings.app_name, lifespan=lifespan)

#Voy a tomar todos los endpoints de este archivo
#Y los voy a agregar a la app principal
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(conversation_router)


