from sourcelyzer.rest.v1.commands.authenticate import AuthCommand
from sourcelyzer.dao import Base, User
import simplejson as json
import cherrypy
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

from sourcelyzer.rest.plugins import SAPlugin
from sourcelyzer.rest.tools import SATool
from sourcelyzer.rest.utils.json import json_error_output
from sourcelyzer.utils import user as userutils
from sourcelyzer.rest.utils.auth import gen_auth_token

from cherrypy.test import helper
from cherrypy.lib.sessions import RamSession

import mock, binascii

def custom_urandom(length):
    return binascii.unhexlify('f' * length)
#    return bytearray('f' * length, encoding='utf-8')
    
class RESTResourceClassTest(helper.CPWebCase):

    interactive = False


    dbfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test.db')

    @mock.patch('os.urandom', side_effect=custom_urandom)
    def setup_server(mock):
        dbfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test.db')
    
        if os.path.exists(dbfile):
            os.remove(dbfile)

        engine = create_engine('sqlite:///%s' % dbfile)

        Base.metadata.create_all(engine)

        SessionMaker = scoped_session(sessionmaker(bind=engine))
        session = SessionMaker

        test_user_one = User(username='test1', password=userutils.gen_passwd_hash('test1pw'))
        test_user_two = User(username='test2', password=userutils.gen_passwd_hash('test2pw'))

        session.add(test_user_one)
        session.add(test_user_two)

        session.commit()
        session.flush()
        session.close()
        SessionMaker.remove()

#        engine.dispose()
#        engine = None
#        session = None

        SAPlugin(cherrypy.engine, 'sqlite:///%s' % dbfile).subscribe()

        satool = SATool()

        cherrypy.tools.db = satool

        cherrypy.config.update({
            'error_page.default': json_error_output,
            'environment': 'test_suite',
            'tools.db.on': True,
            'tools.sessions.on': True,
            'server.thread_pool': 1
        })

        cherrypy.tree.mount(AuthCommand(), '')
    setup_server = staticmethod(setup_server)

    def test_invalid_login(self):

        body = 'username=admin&password=admin'


        headers = [
            ('Content-Length', str(len(body))),
            ('Content-Type', 'application/x-www-form-urlencoded')
        ]

        self.getPage('/login', method='POST', headers=headers, body=body)
        self.assertStatus(401)

    def test_valid_login(self):

        body = 'username=test1&password=test1pw'

        headers = [
            ('Content-Length', str(len(body))),
            ('Content-Type', 'application/x-www-form-urlencoded')
        ]

        self.getPage('/login', method='POST', headers=headers, body=body)

        self.assertStatus(200)

    @mock.patch('os.urandom', side_effect=custom_urandom)
    def test_valid_auth_token_generation(self, mk):

        cherrypy.session = RamSession()

        body = 'username=test2&password=test2pw'

        headers = [
            ('Content-Length', str(len(body))),
            ('Content-Type', 'application/x-www-form-urlencoded')
        ]

        self.getPage('/login', method='POST', headers=headers, body=body)

        output = json.loads(self.body)
        if 'traceback' in output:
            print(output['traceback'])

        self.assertStatus(200)

        session_id = self.cookies[0][1].split(';')[0].split('=')[1]
        print('EXPECTED SESSION ID: %s' % session_id)

        token = gen_auth_token('test2', userutils.gen_passwd_hash('test2pw'), 2, session_id)

        body = json.loads(self.body)

        assert body['token'] == token

    @mock.patch('os.urandom', side_effect=custom_urandom)
    def test_valid_auth_secret(self, mk):

        session_id = 'foobar'

        sess_mock = RamSession()
        sess_mock['user'] = User(username='test1', password=userutils.gen_passwd_hash('test1pw'))

        token = gen_auth_token('test1', userutils.gen_passwd_hash('test1pw'), 2, session_id)


        headers = [
            ('Content-Length', '0'),
            ('Content-Type', 'application/json'),
            ('Authorization', token)
        ]
        cherrypy.session = sess_mock
        cherrypy.session.id = session_id

        token = gen_auth_token('test1', userutils.gen_passwd_hash('test1pw'), 2, session_id)

        self.getPage('/session', method='POST', headers=headers)
        self.assertStatus(204)

