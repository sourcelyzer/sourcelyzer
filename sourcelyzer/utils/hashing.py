import hashlib, os, binascii, sys, io
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sourcelyzer.exceptions import InvalidHashError
from base64 import b64encode, b64decode
def stream_hashsum(ioobj, hasher, blocksize=65536):
    """Generate a hash sum from a filelike object using the supplied hashlib algorithm.

    Example:

        stream_hashsum(open('foobar.txt','rb'), hashlib.md5())

    """
    while True:
        block = ioobj.read(blocksize)
        if len(block) > 0:
            hasher.update(block)
        else:
            break
    return hasher.hexdigest()

def md5sum_file(filename):
    """Generate an MD5 hash sum of the given filename"""
    return stream_hash(open(filename, 'rb'), hashlib.md5())

def sha256sum_file(filename):
    """Generate an SHA256 hash sum of the given filename"""
    return stream_hash(open(filename, 'rb'), hashlib.sha256())

def md5sum_string(content):
    """Generate an MD5 hash sum of a string"""
    return stream_hash(io.BytesIO(content.encode('utf-8')), hashlib.md5())

def sha256sum_string(content):
    """Generate an SHA256 hash sum of a string"""
    return stream_hash(io.BytesIO(content.encode('utf-8')), hashlib.sha256())

def md5sum_stream(ioobj):
    """Generate an MD5 hash sum of a filelike object"""
    return stream_hash(ioobj, hashlib.md5())

def sha256sum_stream(ioobj):
    """Generate an SHA256 hash sum of a filelike object"""
    return stream_hash(ioobj, hashlib.sha256())

def verify_hashsum_stream(ioobj, target_hash, hasher):
    """Verifies a hash sum of a filelike object.

    If the hashes don't match, an InvalidHashError is raised.

    Example:
        verify_hashsum_stream(open('foobar.txt', 'rb'), foobar_md5_sum, hashlib.md5())
    """
    check_hash = stream_hashsum(ioobj, hasher)

    if check_hash != target_hash:
        raise InvalidHashError('Expected %s but got %s' % (target_hash, check_hash))

def verify_hashsum_string(content, target_hash, hasher):
    """Verify the hash sum of a string"""
    verify_hashsum_stream(io.BytesIO(content.encode('utf-8')), target_hash, hasher)


def verify_md5sum_stream(ioobj, target_hash):
    """Verify the MD5 hash sum of a file like object"""
    verify_hashsum_stream(ioobj, target_hash, hashlib.md5())

def verify_sha256sum_stream(ioobj, target_hash):
    """Verify the SHA256 hash sum of a file like object"""
    verify_hashsum_stream(ioobj, target_hash, hashlib.sha256())

def verify_md5sum_string(content, target_hash):
    """Verify the MD5 hash sum of a string"""
    verify_hashsum_stream(io.BytesIO(content.encode('utf-8')), target_hash, hashlib.md5())

def verify_sha256sum_string(content, target_hash):
    """Verify the SHA256 hash sum of a string"""
    verify_hashsum_stream(io.BytesIO(content.encode('utf-8')), target_hash, hashlib.sha256())

def verify_md5sum_file(filename, target_hash):
    """Verify the MD5 hash sum of the given filename"""
    verify_hashsum_stream(open(filename, 'rb'), target_hash, hashlib.md5())

def verify_sha256sum_file(filename, target_hash):
    """Verify the SHA256 hash sum of the given filename"""
    verify_hashsum_stream(open(filename, 'rb'), target_hash, hashlib.sha256())


def gen_passwd_hash(pw):
    ph = PasswordHasher()
    return ph.hash(pw)

def verify_passwd_hash(hs, pw):

    print('VERIFY PASSWD HASH: %s -- %s' % (hs, pw))

    ph = PasswordHasher()
    try:
        ph.verify(hs, pw)
    except VerifyMismatchError as e:
        raise InvalidHashError(e)


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

