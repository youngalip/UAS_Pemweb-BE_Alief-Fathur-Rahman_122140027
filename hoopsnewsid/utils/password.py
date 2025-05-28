import bcrypt

def hash_password(password):
    """Hash a password for storing."""
    pwhash = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
    return pwhash.decode('utf8')

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    return bcrypt.checkpw(provided_password.encode('utf8'), stored_password.encode('utf8'))
