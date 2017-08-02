import cherrypy
from cherrypy.process import wspbus, plugins
from sourcelyzer.plugins.loader import load_plugins

class PluginLoaderPlugin(plugins.SimplePlugin):
    def __init__(self, bus, plugin_dir):
        plugins.SimplePlugin.__init__(self, bus)
        self.plugin_dir = plugin_dir
        self.plugins = None

    def start(self):
        self.refresh_plugins()

        self.bus.subscribe('get-plugins', self.get_plugins)
        self.bus.subscribe('refresh-plugins', self.refresh_plugins)

    def get_plugins(self):
        return self.plugins

    def refresh_plugins(self):
        self.plugins = load_plugins(self.plugin_dir)
        return self.plugins

