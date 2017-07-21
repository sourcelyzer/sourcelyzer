from sourcelyzer.rest.tools import tools
from sourcelyzer.rest.utils import auth
from cherrypy.test import helper
from cherrypy.lib.sessions import RamSession
import cherrypy

class MockResource():

    @cherrypy.expose
    @tools.RequireAuthentication
    def default(self, *vpath, **params):
        return 'done'

class Test_RequireAuthentication(helper.CPWebCase):
    interactive = False

    def setup_server():
        cherrypy.config.update({
            'environment': 'test_suite',
            'tools.sessions.on': True,
            'server.thread_pool': 1
        })

        cherrypy.tree.mount(MockResource(), '/')
    setup_server = staticmethod(setup_server)

    def test_requires_authentication(self):

        username = 'user'
        password = 'pass'
        session_id = 1
        user_id = 1
        token = auth.gen_auth_token(username, password, user_id, session_id)

        cherrypy.session = RamSession()
        cherrypy.session.id = 1

        cherrypy.session['user'] = {
            'id': user_id,
            'username': username,
            'auth': True,
            'token': token
        }

        self.getPage('/')
        print(self.body)
        self.assertStatus(401)

        headers = [
            ('Authorization', token)
        ]

        self.getPage('/', headers=headers)
        print(self.body)
        self.assertStatus(200)




