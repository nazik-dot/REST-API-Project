import hashlib, os

def make_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000).hex()

def hash_password(password):
    salt = os.urandom(16)
    return salt.hex() + ":" + make_hash(password, salt)

def check_password(password, stored):
    salt, h = stored.split(":")
    return make_hash(password, bytes.fromhex(salt)) == h