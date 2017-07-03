from sourcelyzer.logger import get_logger

from sourcelyzer.rest.v1 import HomePage, ProjectResource, UserResource, AuthCommand, PluginsResource
from sourcelyzer.rest.utils.json import json_error_output, json_processor
from sourcelyzer.rest.plugins.sqlalchemy import SAPlugin
from sourcelyzer.rest.plugins.plugin_loader import PluginLoaderPlugin
from sourcelyzer.rest.tools import SATool

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import cherrypy
import threading

import logging
import time

import os


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

        PluginLoaderPlugin(cherrypy.engine, self._config['sourcelyzer.plugin_dir']).subscribe()
        SAPlugin(cherrypy.engine, self._config['sourcelyzer.db.uri']).subscribe()

        cherrypy.tools.db = SATool()

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

        cherrypy.tree.mount(HomePage(), '/', {'/': {
            'tools.gzip.on': True,
            'tools.staticdir.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd()) + '/web-ui',
            'tools.staticdir.dir': './'
        }})
        cherrypy.tree.mount(ProjectResource(), '/rest/v1/projects', {'/': {
            'error_page.default': json_error_output
        }})
        cherrypy.tree.mount(UserResource(), '/rest/v1/users', {'/': {
            'error_page.default': json_error_output
        }})
        cherrypy.tree.mount(PluginsResource(), '/rest/v1/plugins')

        cherrypy.tree.mount(AuthCommand(), '/rest/v1/commands/authenticate', {'/login': {
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
        self.logger = get_logger('sourcelyzer')

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

