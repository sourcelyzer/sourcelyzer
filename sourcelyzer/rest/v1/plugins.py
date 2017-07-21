from sourcelyzer.rest.v1.base import RESTResource
from sourcelyzer.rest.tools import RequireAuthentication
import cherrypy
import os
import zipfile
import io
import glob


class Plugins():

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @RequireAuthentication
    def default(self, *vpath, **params):
        plugins = cherrypy.engine.publish('get-plugins').pop()
        cherrypy.response.headers['Content-Type'] = 'application/json'

        if len(vpath) == 0:
            output = {}

            for plugin_type in plugins:
                output[plugin_type] = []
                for plugin in plugins[plugin_type]:
                    output[plugin_type].append(plugin)
            return output
        elif len(vpath) == 1:
            print(plugins)
            plugin_type = vpath[0]

            if plugin_type not in plugins:
                raise cherrypy.HTTPError(404, 'Plugin type %s not found' % plugin_type)

            output = []

            for plugin in plugins[plugin_type]:
                output.append(plugin)

            return output
        elif len(vpath) == 2:
            plugin_type = vpath[0]
            plugin = vpath[1]

            if plugin_type not in plugins:
                raise cherrypy.HTTPError(404, 'Plugin type %s not found' % plugin_type)
            if plugin not in plugins[plugin_type]:
                raise cherrypy.HTTPError(404, 'Plugin %s not found' % plugin)

            if 'download' in params and params['download'] == 'true':

                mod = plugins[plugin_type][plugin]

                dirname = os.path.dirname(os.path.realpath(mod.__file__))

                zipcontents = io.BytesIO()
                zf = zipfile.ZipFile(zipcontents, 'w')

                for fn in glob.glob(dirname + '/**', recursive=True):

                    destfn = fn.replace(dirname, '')

                    if '__pycache__' in fn:
                        continue
                    zf.write(fn, '/%s/%s/%s' % (plugin_type, plugin, destfn))

                zf.close()
                cherrypy.response.headers['Content-Type'] = 'application/zip'
                cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="%s.zip"' % plugin
                return zipcontents.getvalue()
            else:
                output = {
                    'name': plugin,
                    'path': os.path.dirname(os.path.realpath(plugins[plugin_type][plugin].__file__))
                }

                return output


