from sourcelyzer.rest.common import DBResource
from sourcelyzer.dao.user import User
from sourcelyzer.utils.hashing import gen_passwd_hash
import cherrypy

class UserResource(DBResource):
    skipfields = ['id', 'last_modified', 'created_on', 'password']
    resource = User

    def handle_POST(self, *vpath, **params):
        if 'password' in cherrypy.request.json:
            cherrypy.request.json['password'] = gen_passwd_hash(cherrypy.request.json['password'])
        return DBResource.handle_POST(self, *vpath, **params)

