import bcrypt

def hash_password(plain_text_password):
    """
    Hash the plain text password using bcrypt and return the hashed password as a string.
    """
    hashed = bcrypt.hashpw(plain_text_password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def check_password(plain_text_password, hashed_password):
    """
    Check if the provided plain text password matches the hashed password.
    Returns True if they match, False otherwise.
    """
    return bcrypt.checkpw(plain_text_password.encode('utf-8'), hashed_password.encode('utf-8'))
