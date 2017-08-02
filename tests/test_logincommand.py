import simplejson as json
import cherrypy, sys, os, binascii
from pprint import pprint

from sourcelyzer.httpapi.utils.json import json_error_output
from sourcelyzer.httpapi.v1.commands import LoginCommand, SessionCommand
from sourcelyzer.httpapi.tools.sqlalchemy import SATool
from sourcelyzer.utils.hashing import gen_passwd_hash, gen_auth_token

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sourcelyzer.dao.base import Base

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from cherrypy.test import helper
from cherrypy.lib.sessions import RamSession

import mock

def custom_urandom(length):
    s = 'f' * length;
    return s.encode('utf-8')


class UserDao(Base):
    __tablename__ = 'test_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String)
    password = Column(String)

def setup_db():
    dbfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test.db')

    if os.path.exists(dbfile):
        os.remove(dbfile)

    engine = create_engine('sqlite:///%s' % dbfile)

    Base.metadata.create_all(engine)

    SessionMaker = sessionmaker(bind=engine)
    session = SessionMaker()

    test_user_one = UserDao(username='test1', password=gen_passwd_hash('test1pw'))
    test_user_two = UserDao(username='test2', password=gen_passwd_hash('test2pw'))

    session.add(test_user_one)
    session.add(test_user_two)

    session.commit()
    session.flush()
    session.close()

    engine.dispose()
    engine = None

class LoginCommandTest(helper.CPWebCase):

    interactive = False

    def setUp(self):
        setup_db()

    def tearDown(self):
        dbfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test.db')
        os.remove(dbfile)

    def setup_server():

        dbfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test.db')

        satool = SATool(dburi='sqlite:///%s' % dbfile)
        cherrypy.tools.db = satool

        cherrypy.config.update({
            'error_page.default': json_error_output,
            'environment': 'test_suite',
            'tools.db.on': True,
            'tools.sessions.on': True,
            'server.thread_pool': 1
        })

        cherrypy.tree.mount(LoginCommand(UserDao), '/login')
        cherrypy.tree.mount(SessionCommand(UserDao), '/session')

    def test_good_login(self):

        cherrypy.session = RamSession()

        self.getPage('/login', method='POST', body='username=test1&password=test1pw')
        pprint(json.loads(self.body))
        self.assertStatus(200)

        body = json.loads(self.body.decode('utf-8'))

        assert body['session'] == cherrypy.session.id

        assert cherrypy.session['user']['id'] == 1
        assert cherrypy.session['user']['username'] == 'test1'
        assert cherrypy.session['user']['auth'] == True
        assert cherrypy.session['user']['token'] == body['token']

        del cherrypy.session

    @mock.patch('os.urandom', side_effect=custom_urandom)
    def test_good_session(self,mock):

        cherrypy.session = RamSession()


        user = cherrypy.tools.db.session.query(UserDao).filter(UserDao.id == 2).first()



        token = gen_auth_token('test2', user.password, 2, cherrypy.session.id)
        cherrypy.session['user'] = {} 
        cherrypy.session['user']['id'] = 2
        cherrypy.session['user']['username'] = 'test2'
        cherrypy.session['user']['auth'] = True
        cherrypy.session['user']['token'] = token

        self.getPage('/session', method='POST', headers=[('Authorization', token)])
        print('GOOD SESSION: %s' % self.body)
        self.assertStatus(204)

        del cherrypy.session


    def test_bad_password(self):
        self.getPage('/login', method='POST', body='username=test1&password=bad_pw')
        pprint(json.loads(self.body))
        self.assertStatus(401)

    def test_bad_username(self):
        self.getPage('/login', method='POST', body='username=bad_user&password=test1pw')
        self.assertStatus(401)

