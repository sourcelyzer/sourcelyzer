from sourcelyzer.rest.v1.base import DBResource
from sourcelyzer.dao import User

class UserResource(DBResource):
    resource = User 

