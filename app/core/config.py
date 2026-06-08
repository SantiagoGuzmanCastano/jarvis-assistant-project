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
    access_token_expire_minutes: int = 30

    #python hace el mapeo automaticamente por nombre
    #detecta que en .env hay un JWT_SECRET_KEY y lo asigna
    #al jwt_secret_key que esta definido arribita
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

#Este codigo me permite hacer
#settings.app_name
#settings.environment
#en cualquier archivo en vez de hardcodear
#el nombre siempre