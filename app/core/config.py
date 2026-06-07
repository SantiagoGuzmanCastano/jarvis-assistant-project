#------------------------------------------------------------

#CONFIGURACION INICIAL DEL PROYECTO

#------------------------------------------------------------



from pydantic_settings import BaseSettings

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

settings = Settings()

#Este codigo me permite hacer
#settings.app_name
#settings.environment
#en cualquier archivo en vez de hardcodear
#el nombre siempre