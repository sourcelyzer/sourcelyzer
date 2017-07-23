from sourcelyzer.logging import init_logger

from sourcelyzer.rest.utils.json import json_error_output, json_processor
from sourcelyzer.rest.plugins.plugin_loader import PluginLoaderPlugin

import cherrypy
import threading

import logging
import time

import os

from sourcelyzer.rest.tools import SATool

from sourcelyzer.rest.v1.resources.user import UserResource
from sourcelyzer.rest.v1.resources.project import ProjectResource
from sourcelyzer.rest.v1.commands import LoginCommand
from sourcelyzer.rest.v1.plugins import Plugins as PluginsResource

from sourcelyzer.dao import User, PluginRepository

import requests

def refresh_plugins(dbsession):

    try:
        for row in dbsession.query(PluginRepository).all():
            url = row.url

            r = requests.get(url + '/plugins.json')
            print(r.text)
    finally:
        dbsession.close()
 


class ServerThread(threading.Thread):

    def __init__(self, config, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self._running = False
        self._config = config

        self.homedir = os.path.expanduser('~/.sourcelyzer')
        self.sessiondir = os.path.join(self.homedir, 'sessions')

    def isRunning(self):
        return self._running

    def run(self):

        if not os.path.exists(self.homedir):
            os.makedirs(self.homedir)

        if not os.path.exists(self.sessiondir):
            os.makedirs(self.sessiondir)

        # PluginLoaderPlugin(cherrypy.engine, self._config['sourcelyzer.plugin_dir']).subscribe()
 #        SAPlugin(cherrypy.engine, self._config['sourcelyzer.db.uri']).subscribe()

        cherrypy.tools.db = SATool(dburi=self._config['sourcelyzer.db.uri'])

        # refresh_plugins(cherrypy.tools.db.session())

        cherrypy.config.update({
            'server.socket_host': self._config['sourcelyzer.server.listen_addr'],
            'server.socket_port': int(self._config['sourcelyzer.server.listen_port']),
            'tools.json_in.processor': json_processor,
            'tools.sessions.on': True,
            'tools.sessions.storage_class': cherrypy.lib.sessions.FileSession,
            'tools.sessions.storage_path': self.sessiondir,
            'tools.sessions.name': 'sourcelyzer',
            'tools.sessions.timeout': 60,
            'tools.sessions.debug': True,
            'tools.sessions.path': None,
            'tools.db.on': True,
            'error_page.default': json_error_output
        })




        """
        cherrypy.tree.mount(HomePage(), '/', {'/': {
            'tools.gzip.on': True,
            'tools.staticdir.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd()) + '/web-ui',
            'tools.staticdir.dir': './'
        }})

        """
        cherrypy.tree.mount(ProjectResource(), '/rest/v1/projects', {'/': {
            'error_page.default': json_error_output
        }})

        """
        cherrypy.tree.mount(UserResource(), '/api/users', {'/': {
        }})
        """
        cherrypy.tree.mount(PluginsResource(), '/rest/v1/plugins')

        cherrypy.tree.mount(LoginCommand(User), '/rest/v1/commands/authenticate', {'/login': {
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

