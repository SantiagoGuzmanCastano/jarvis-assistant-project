from fastapi import FastAPI
from core.config import settings

#Voy a tomar todos los endpoints de este archivo
from routers.health import router as health_router


app = FastAPI(title=settings.app_name)


#Voy a tomar todos los endpoints de este archivo
#Y los voy a agregar a la app principal
app.include_router(health_router)


