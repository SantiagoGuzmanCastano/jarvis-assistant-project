
from fastapi import APIRouter


#Creamos un objeto Router
#Este objeto guarda todos los endpoints
#De estearchivo
router = APIRouter()

#Todos estos endpoints
@router.get("/health")
def health_check():
    return {
        'status': 'ok',
        'service': 'jarvis-backend'
    }
