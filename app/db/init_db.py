#------------------------------------------------------------

#CREACION DE TABLAS DE LA DB

#------------------------------------------------------------

from app.db.base import Base
from app.db.session import engine

#estos de aca abajo son los imports de los
# modelos de nuestra base de datos
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user_settings import UserSettings



def create_db_tables():
    Base.metadata.create_all(bind=engine)

    #Base.metadata = guarda todas las clases modelos de las dbs que heredan de base
    #Toda clase que hereda de Base y define __tablename__ representa una tabla,
    #y metadata guarda las variables de esa clase modelo, ejemplo
    #tabla users
    #id
    #email
    #hashed_password
    #created_at