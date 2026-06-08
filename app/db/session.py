#------------------------------------------------------------

#CONEXION A BASE DE DATOS Y FABRICA DE SESIONES

#------------------------------------------------------------

from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

#1. Conexion
engine = create_engine(settings.database_url)

#2. Sesión o conversacion de modificacion con db

#Fábrica de sesiones de base de datos.
SessionLocal = sessionmaker(
    #Los cambios no se guardan automáticamente. Nosotros decidimos cuándo hacer commit.
    autocommit=False,

    #SQLAlchemy no empuja cambios pendientes antes de cada query automáticamente.
    autoflush= False,
    bind=engine
)

def get_session():

    with SessionLocal() as session:
        yield session


SessionDep= Annotated[Session, Depends(get_session)]