from sourcelyzer.rest.v1 import RESTResource
from sourcelyzer.dao import User
from sourcelyzer.rest.tools import RequiredParam, RequireAuthentication
from sourcelyzer.utils import user as userutils
from sourcelyzer.rest.utils import auth as authutils
import cherrypy

class AuthCommand():

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @RequiredParam('username')
    @RequiredParam('password')
    def login(self, username, password):

        try:
            user = userutils.get_user_by_username(username, cherrypy.request.db)
            userutils.verify_passwd(password, user.password)

            token = authutils.gen_auth_token(user.username, user.password, user.id, cherrypy.session.id)

            cherrypy.session['user'] = user

            return {
                'token': token
            }
        except (userutils.InvalidPassword, userutils.UserNotFound) as e:
            cherrypy.log('Login Error', traceback=True)
            raise cherrypy.HTTPError(401)


    @cherrypy.expose
    @RequireAuthentication
    def session(self):
        cherrypy.response.status = 204

