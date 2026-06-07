#------------------------------------------------------------

#CREACION DE CLASE BASE PARA LOS MODELS DE LA DATABASE

#------------------------------------------------------------

#Aca no usaremos SQLMODEL para crear nuestros modelos de nuestra Base de datos, usaremos
#SQLALCHEMY, para eso necesitamos crear una clase base para todos nuestro modelos de la db.


from sqlalchemy.orm import DeclarativeBase


#Base comun para todos los modelos de la DB.
class Base(DeclarativeBase):
    pass