from sourcelyzer.logging import init_logger

from sourcelyzer.httpapi.utils.json import json_error_output, json_processor
from sourcelyzer.httpapi.plugins.plugin_loader import PluginLoaderPlugin

import cherrypy
import threading

import logging
import time

import os

from sourcelyzer.httpapi.tools import SATool

from sourcelyzer.httpapi.v1.resources.user import UserResource
from sourcelyzer.httpapi.v1.resources.project import ProjectResource
from sourcelyzer.httpapi.v1.commands import LoginCommand, SessionCommand
from sourcelyzer.httpapi.v1.plugins import Plugins as PluginsResource

from sourcelyzer.dao import User, PluginRepository

import requests

from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import EchoWebSocket, WebSocket

from collections import deque
try:
    import simplejson as json
except ImportError:
    import json

def refresh_plugins(dbsession):

    try:
        for row in dbsession.query(PluginRepository).all():
            url = row.url

            r = requests.get(url + '/plugins.json')
            print(r.text)
    finally:
        dbsession.close()
 

class PidReader(WebSocket):

    def __init__(self, *args, **kwargs):
        WebSocket.__init__(self, *args, **kwargs)
        self.messages = deque([])
        self.broadcast = False

    def get_message(self, packet):

        self.messages.append(packet)

        while self.messages:
            msg = self.messages.popleft()
            if msg != None:
                self.send(json.dumps(msg))

    def received_message(self, msg):

        cmd = json.loads(msg.data.decode('utf-8'));

        if cmd['cmd'] == 'bg-listen':
            
            self.send('Listening to the background noises')
            cherrypy.engine.subscribe('bg-noise', self.get_message)

    
class WsHandler(object):
    @cherrypy.expose
    def index(self, **params):
        cherrypy.engine.publish('task-%s' % params.get('pid'), params.get('msg'), params.get('pid'))

    @cherrypy.expose
    def ws(self):
        pass


class ServerThread(threading.Thread):

    def __init__(self, config, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self._running = False
        self._config = config

        self.data_dir = os.path.expanduser(self._config['sourcelyzer.data_dir'])
        self.session_dir = os.path.join(self.data_dir, 'sessions')
        self.plugin_dir = os.path.join(self.data_dir, 'plugins')

    def isRunning(self):
        return self._running

    def run(self):

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        if not os.path.exists(self.session_dir):
            os.makedirs(self.session_dir)

        # PluginLoaderPlugin(cherrypy.engine, self._config['sourcelyzer.plugin_dir']).subscribe()
 #        SAPlugin(cherrypy.engine, self._config['sourcelyzer.db.uri']).subscribe()

        WebSocketPlugin(cherrypy.engine).subscribe()
        cherrypy.tools.websocket = WebSocketTool()

        cherrypy.tools.db = SATool(dburi=self._config['sourcelyzer.db.uri'])

        # refresh_plugins(cherrypy.tools.db.session())

        cherrypy.config.update({
            'server.socket_host': self._config['sourcelyzer.server.listen_addr'],
            'server.socket_port': int(self._config['sourcelyzer.server.listen_port']),
            'tools.json_in.processor': json_processor,
            'tools.sessions.on': True,
            'tools.sessions.storage_class': cherrypy.lib.sessions.FileSession,
            'tools.sessions.storage_path': self.session_dir,
            'tools.sessions.name': 'sourcelyzer',
            'tools.sessions.timeout': 10,
            'tools.sessions.clean_freq': 8,
            'tools.sessions.debug': True,
            'tools.sessions.path': None,
            'tools.db.on': True,
            'error_page.default': json_error_output
        })



        cherrypy.tree.mount(WsHandler(), '/ws', {'/ws': {
            'tools.websocket.on': True,
            'tools.websocket.handler_cls': PidReader
            }})

        """
        cherrypy.tree.mount(HomePage(), '/', {'/': {
            'tools.gzip.on': True,
            'tools.staticdir.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd()) + '/web-ui',
            'tools.staticdir.dir': './'
        }})

        """
        cherrypy.tree.mount(ProjectResource(), '/httpapi/v1/projects', {'/': {
            'error_page.default': json_error_output
        }})

        """
        cherrypy.tree.mount(UserResource(), '/api/users', {'/': {
        }})
        """
        cherrypy.tree.mount(PluginsResource(config=self._config), '/httpapi/v1/plugins')

        cherrypy.tree.mount(LoginCommand(User), '/httpapi/v1/commands/authenticate', {'/login': {
            'error_page.default': json_error_output
        }})

        cherrypy.tree.mount(SessionCommand(User), '/httpapi/v1/commands/session', {'/': {
            'error_page.default': json_error_output
        }})

        print('starting server at http://%s:%s' % (
            self._config['sourcelyzer.server.listen_addr'],
            self._config['sourcelyzer.server.listen_port']
        ), flush=True)
        cherrypy.engine.start()
        cherrypy.engine.block()

    def stop(self):
        cherrypy.engine.stop()
        cherrypy.engine.exit()



class App():
    def __init__(self, config):
 
        self.config = config
        self._running = False
        init_logger('sourcelyzer')
        self.logger = logging.getLogger('sourcelyzer')

    def isRunning(self):
        return self._running

    def init_logger(self):
        pass

    def run(self):

        self._running = True

        server = ServerThread(self.config)
        server.start()

        while self._running:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                server.stop()
                self._running = False

