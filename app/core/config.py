from pydantic_settings import BaseSettings

# Clase de pydantic especializada para configuracion. 
# Puede leer valores de environment tables
class Settings(BaseSettings):

    app_name: str = "Jarvis Backend"
    # Donde está corriendo el backend
    environment: str = "development"

settings = Settings()

#Este codigo me permite hacer
#settings.app_name
#settings.environment
#en cualquier archivo en vez de hardcodear
#el nombre siempre