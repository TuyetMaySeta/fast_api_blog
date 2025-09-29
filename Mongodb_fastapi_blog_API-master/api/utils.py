from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    # Cắt password về 72 ký tự để tránh lỗi bcrypt
    if isinstance(plain_password, str):
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # Cắt password về 72 ký tự để tránh lỗi bcrypt
    if isinstance(password, str):
        password = password[:72]
    return pwd_context.hash(password)