#------------------------------------------------------------

#CONFIGURACION INICIAL DEL PROYECTO

#------------------------------------------------------------



from pydantic_settings import BaseSettings, SettingsConfigDict

# Clase de pydantic especializada para configuracion. 
# Puede leer valores de environment tables
class Settings(BaseSettings):

    app_name: str = "Jarvis Backend"
    # Donde está corriendo el backend
    environment: str = "development"

    #aca definimos la url de la db postgres, esta url la creamos nosotros con esto en mente:
    #postgresql+driver://usuario:contraseña@host:puerto/base_de_datos
    #psycopg es el driver que permite que python hable con psql
    database_url: str = "postgresql+psycopg://jarvis_user:jarvis_password@localhost:5432/jarvis_db"
    #El usuario y contraseña se ponen para autenticarse contra PostgreSQL y que te deje acceder a esa base de datos.

    jwt_secret_key: str
    jwt_alrogithm: str = "HS256"
    access_token_expire_minutes: int
    refresh_token_expire_days: int = 7

    gemini_api_key: str

    token_encryption_key: str
    refresh_token_hash_key: str

    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    google_request_timeout_seconds: float = 15.0

    tool_state_expire_minutes: int = 15

    #python hace el mapeo automaticamente por nombre
    #detecta que en .env hay un JWT_SECRET_KEY y lo asigna
    #al jwt_secret_key que esta definido arribita, lo mismo con gemini_api_key
    model_config = SettingsConfigDict(env_file=".env")

    cors_allowed_origins: list[str] = []


settings = Settings()

#Este codigo me permite hacer
#settings.app_name
#settings.environment
#en cualquier archivo en vez de hardcodear
#el nombre siempre
