import hashlib

def verify_password(plain_password, hashed_password):
    """Verify password using SHA256"""
    hashed = hashlib.sha256(plain_password.encode()).hexdigest()
    return hashed == hashed_password

def get_password_hash(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()