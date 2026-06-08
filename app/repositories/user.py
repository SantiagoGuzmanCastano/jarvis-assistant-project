#------------------------------------------------------------

#

#------------------------------------------------------------


from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User

def get_user_by_email(email: str, session: Session) -> User | None:
    statement = select(User).where(User.email == email)

    #Ejecuta la consulta y devuelve el primer objeto User encontrado.

    #scalar es el que devuelve el primero, es lo mismo que
    #result = session.execute(statement)
    #user = result.scalar_one_or_none()
    return session.scalar(statement)


def create_user(email: str, hashed_password: str, session: Session) -> User:

    new_user = User(
        email= email,
        hashed_password=hashed_password
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user