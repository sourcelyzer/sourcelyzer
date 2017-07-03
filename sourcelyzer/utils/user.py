from sourcelyzer.dao import User
from argon2 import PasswordHasher

class UserNotFound(Exception):
    """User Not Found exception

    Thrown whenever we have to look up a specific user
    by ID or username but it is not found
    """
    pass


class InvalidPassword(Exception):
    """Invalid Password Exception

    Thrown whenever a password comparison fails
    """
    pass

def get_user_by_username(username, session):
    user = session.query(User).filter(User.username == username).first()
    if not user:
        raise UserNotFound('User %s not found in database' % username)
    return user

def get_user_by_id(userid, session):
    user = session.query(User).filter(User.id == userid).first()
    if not user:
        raise UserNotFound('User ID %s not found in database' % userid)
    return user

def gen_passwd_hash(pw):
    ph = PasswordHasher()
    return ph.hash(pw)

def verify_passwd(pw, hs):
    ph = PasswordHasher()
    ph.verify(hs, pw)


if __name__ == "__main__":

    pw = 'foobar'

    pwhash = gen_passwd_hash(pw)
    print('hash: %s' % pwhash)

    verify_passwd(pw, pwhash)
    print('good')
