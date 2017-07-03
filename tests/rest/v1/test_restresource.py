from sourcelyzer.rest.v1.base import RESTResource
from sourcelyzer.rest.utils.json import json_error_output
import simplejson as json
import cherrypy, sys

from cherrypy.test import helper

class RESTResourceClassTest(helper.CPWebCase):

    interactive = False

    def setup_server():

        class RESTResourceImpl(RESTResource):
            def handle_GET(self, *vpath, **params):
                return {'ok': True}


        cherrypy.config.update({
            'error_page.default': json_error_output,
            'environment': 'test_suite'
        })

        cherrypy.tree.mount(RESTResourceImpl(), '')
    setup_server = staticmethod(setup_server)

    def test_handles_get(self):
        self.getPage('/')
        self.assertStatus(200)
        self.assertHeader('Content-Type', 'application/json')
        self.assertBody('{"ok": true}')

    def test_handles_invalid_post(self):

        headers = [
            ('Content-Type', 'application/json'),
            ('Content-Length', '2')
        ]

        self.getPage('/', method='POST', headers=headers, body='{}')
        self.assertStatus(405)
        self.assertHeader('Content-Type', 'application/json')
        self.assertHeader('Allow', 'GET')

    def test_handles_invalid_put(self):

        headers = [
            ('Content-Type', 'application/json'),
            ('Content-Length', '2')
        ]

        self.getPage('/', method='PUT', headers=headers, body='{}')
        self.assertStatus(405)
        self.assertHeader('Content-Type', 'application/json')
        self.assertHeader('Allow', 'GET')

        body = json.loads(self.body.decode('utf-8'))
        print('body? %s' % body)
        
        assert body['status'] == 405

