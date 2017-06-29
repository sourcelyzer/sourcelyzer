from base64 import b64encode
import hashlib
import os

def gen_auth_token(user, session_id):
    salty = b64encode(os.urandom(512)).hex()
    hashthis = '%s-%s-%s-%s' % (user.username, user.password, user.id, salty)
    token = hashlib.sha256(hashthis.encode('utf-8')).hexdigest()

    secret = '%s%s' % (token, session_id)

    return (token, hashlib.sha256(secret.encode('utf-8')).hexdigest())

def check_auth_token(token, secret, session_id):

    sess_secret = '%s%s' % (token, session_id)

    return hashlib.sha256(sess_secret.encode('utf-8')).hexdigest() == secret

