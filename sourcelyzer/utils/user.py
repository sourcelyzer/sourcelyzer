from sourcelyzer.dao import User
from argon2 import PasswordHasher
from sourcelyzer.exceptions import UserNotFound, InvalidPassword

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

