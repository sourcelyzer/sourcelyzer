from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import os, hashlib
from base64 import b64encode, b64decode

class InvalidAuthToken(Exception):
    pass

class InvalidHash(Exception):
    pass

def gen_passwd_hash(pw, **kwargs):
    ph = PasswordHasher(**kwargs)
    return ph.hash(pw)

def verify_hash(hs, pw):
    ph = PasswordHasher()
    try:
        ph.verify(hs, pw)
    except VerifyMismatchError as e:
        raise InvalidHash(e)

def gen_auth_token(username, password, userid, session_id, encoding='utf-8'):
    salt = os.urandom(128)

    if isinstance(session_id, str):
        session_id = session_id.encode(encoding)
    elif isinstance(session_id, int):
        session_id = bytes([session_id])
    else:
        session_id = str(session_id).encode(encoding)

    token = hashlib.sha256()
    token.update(username.encode(encoding))
    token.update(password.encode(encoding))
    token.update(bytes([userid]))
    token.update(session_id)
    token.update(salt)

    b64salt  = b64encode(salt).decode('utf-8')
    b64token = b64encode(token.digest()).decode('utf-8')

    return '%s/%s' % (b64salt, b64token)

def verify_auth_token(token, username, password, userid, session_id, encoding='utf-8'):
    b64salt = token[0:172]
    salt = b64decode(b64salt.encode('utf-8'))

    if isinstance(session_id, str):
        session_id = session_id.encode(encoding)
    elif isinstance(session_id, int):
        session_id = bytes([session_id])
    else:
        session_id = str(session_id).encode(encoding)

    expected_token = hashlib.sha256()
    expected_token.update(username.encode(encoding))
    expected_token.update(password.encode(encoding))
    expected_token.update(bytes([userid]))
    expected_token.update(session_id)
    expected_token.update(salt)

    b64token = b64encode(expected_token.digest()).decode('utf-8')

    new_token = '%s/%s' % (b64salt, b64token)

    if token != new_token:
        raise InvalidAuthToken()

