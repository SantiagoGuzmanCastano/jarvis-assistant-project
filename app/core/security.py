from passlib.context import CryptContext


# 1: HASHEAR CONTRASEÑA
# CryptContext configura el algoritmo de hashing que se va a usar
# schemes=["bcrypt"] le dice que use bcrypt para hashear y verificar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated ="auto")

# Convierte la contraseña real en un string irreversible para guardar en la DB
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# 2: VERIFICAMOS LA CONTRASEÑA
# COMPARAMOS LA CONTRASEÑA DEL LOGIN CON EL HASH GUARDADO
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)