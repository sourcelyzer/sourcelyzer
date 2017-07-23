from sourcelyzer.dao.base import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sourcelyzer.rest.utils.json import json_error_output
from sourcelyzer.rest.v1.resources.base import DBResource
from sourcelyzer.rest.plugins.sqlalchemy import SAPlugin
from sourcelyzer.rest.tools.sqlalchemy import SATool
from sourcelyzer.utils.hashing import gen_passwd_hash
import os
import cherrypy
from cherrypy.test import helper
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import simplejson as json

class TestDao(Base):
    __tablename__ = 'test_table'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String)
    password = Column(String)

def setup_db():
    dbfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test.db')

    print('dbfile:%s' % dbfile)

    if os.path.exists(dbfile):
        os.remove(dbfile)

    engine = create_engine('sqlite:///%s' % dbfile)

    Base.metadata.create_all(engine)

    SessionMaker = sessionmaker(bind=engine)
    session = SessionMaker()

    test_user_one = TestDao(username='test1', password=gen_passwd_hash('test1pw'))
    test_user_two = TestDao(username='test2', password=gen_passwd_hash('test2pw'))

    session.add(test_user_one)
    session.add(test_user_two)

    session.commit()
    session.flush()
    session.close()

    engine.dispose()
    engine = None


class DBResourceImpl(DBResource):
    resource = TestDao

class DBResourceClassTest(helper.CPWebCase):

    interactive = False

    def setUp(self):
        setup_db()
        helper.CPWebCase.setUp(self)

    def setup_server():

        setup_db()

        dbfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test.db')
       # SAPlugin(cherrypy.engine, 'sqlite:///%s' % dbfile).subscribe()

        satool = SATool(dburi='sqlite:///%s' % dbfile)

        cherrypy.tools.db = satool

        cherrypy.config.update({
            'error_page.default': json_error_output,
            'environment': 'test_suite',
            'tools.db.on': True,
            'tools.sessions.on': True,
            'server.thread_pool': 1
        })

        cherrypy.tree.mount(DBResourceImpl(), '')
    setup_server = staticmethod(setup_server)


    def test_handles_get_all(self):
        self.getPage('/')
        self.assertStatus(200)
        self.assertHeader('Content-Type', 'application/json')

        body = json.loads(self.body.decode('utf-8'))

        assert body[0]['id'] == 1
        assert body[0]['username'] == 'test1'
        assert body[1]['id'] == 2
        assert body[1]['username'] == 'test2'

    def test_handles_get_one(self):
        self.getPage('/1')

        self.assertStatus(200)
        self.assertHeader('Content-Type', 'application/json')

        body = json.loads(self.body.decode('utf-8'))

        assert body['id'] == 1
        assert body['username'] == 'test1'

    def test_handles_post(self):

        input_body = {
            'username': 'test3',
            'password': gen_passwd_hash('test3pw')
        }

        input_body = json.dumps(input_body)

        headers = [
            ('Content-Length', str(len(input_body))),
            ('Content-Type', 'application/json')
        ]

        self.getPage('/', method='POST', body=input_body.encode('utf-8'), headers=headers)

        body = json.loads(self.body.decode('utf-8'))

        assert body['id'] == 3
        assert body['username'] == 'test3'


    def test_handles_delete(self):
        self.getPage('/2', method='DELETE')
        self.assertStatus(200)

        body = json.loads(self.body.decode('utf-8'))

        assert body['ok'] == True

    def test_handles_delete_not_found(self):
        self.getPage('/100', method='DELETE')
        self.assertStatus(404)

    def test_handles_put_not_found(self):

        body = '{}'
        headers = [
            ('Content-Length', '2'),
            ('Content-Type', 'application/json')
        ]

        self.getPage('/1011', method='PUT', headers=headers, body=body.encode('utf-8'))
        self.assertStatus(404)

    def test_handles_put(self):

        input_body = {
            'username': 'test-changed'
        }

        input_body = json.dumps(input_body)

        headers = [
            ('Content-Length', str(len(input_body))),
            ('Content-Type', 'application/json')
        ]

        self.getPage('/1', method='PUT', body=input_body.encode('utf-8'), headers=headers)

        body = json.loads(self.body.decode('utf-8'))

        print(body)

        assert body['id'] == 1
        assert body['username'] == 'test-changed'


