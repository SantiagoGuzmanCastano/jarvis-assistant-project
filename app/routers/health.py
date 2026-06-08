
from fastapi import APIRouter

from app.schemas.health import HealthResponse


#Creamos un objeto Router
#Este objeto guarda todos los endpoints
#De estearchivo
router = APIRouter()

#Todos estos endpoints
@router.get("/health", response_model=HealthResponse)
def health_check():
    return {
        'status': 'ok',
        'service': 'jarvis-backend'
    }
