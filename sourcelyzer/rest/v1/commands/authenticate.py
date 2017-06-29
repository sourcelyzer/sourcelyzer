from sourcelyzer.rest.v1 import RESTResource
from sourcelyzer.dao import User
from sourcelyzer.utils.pw import compare_pass
from sourcelyzer.rest.tools import RequiredParam, RequireAuthentication
from sourcelyzer.rest.utils import gen_auth_token, check_auth_token
import cherrypy

class AuthCommand():

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @RequiredParam('username')
    @RequiredParam('password')
    def login(self, username, password):
        
        session = cherrypy.request.db

        user = session.query(User).filter(User.username == username).first()

        if not user:
            raise cherrypy.HTTPError(401)

        if compare_pass(password.encode('utf-8'), user.password):

            token, secret = gen_auth_token(user, cherrypy.session.id.encode('utf-8'))

            cherrypy.session['user'] = {
                'id': user.id,
                'username': username,
                'auth': True,
                'secret': secret
            }

            return {
                'token': token
            }
        else:
            raise cherrypy.HTTPError(401)

    @cherrypy.expose
    @RequireAuthentication
    def session(self):
        cherrypy.response.status = 204

