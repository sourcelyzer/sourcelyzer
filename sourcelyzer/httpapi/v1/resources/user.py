from sourcelyzer.httpapi.v1.resources.base import DBResource
from sourcelyzer.dao import User

class UserResource(DBResource):
    resource = User 

