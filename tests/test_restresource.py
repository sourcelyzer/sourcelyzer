import simplejson as json
import cherrypy, sys

from sourcelyzer.rest.utils.json import json_error_output
from sourcelyzer.rest.common.resources import RESTResource
from cherrypy.test import helper

class RESTResourceClassTest(helper.CPWebCase):

    interactive = False

    def setup_server():

        class RESTResourceImpl(RESTResource):
            def handle_GET(self, *vpath, **params):
                return {'ok': True}

            def handle_POST(self, *vpath, **params):
                return {'post_ok': True}

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

    def test_handles_invalid_put(self):

        headers = [
            ('Content-Type', 'application/json'),
            ('Content-Length', '2')
        ]

        self.getPage('/', method='PUT', headers=headers, body='{}')
        self.assertHeader('Content-Type', 'application/json')
        self.assertHeader('Allow', 'GET,POST')

    def test_handles_valid_post(self):

        headers = [
            ('Content-Type', 'application/json'),
            ('Content-Length', '2')
        ]

        self.getPage('/', method='POST', headers=headers, body='{}')
        self.assertStatus(200)
        self.assertHeader('Content-Type', 'application/json')
        self.assertBody('{"post_ok": true}')


