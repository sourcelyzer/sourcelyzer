import cherrypy
import simplejson as json

def json_processor(entity):
    if entity.length == 0 or entity.length == '0':
        cherrypy.service.request.json = None
        return

    if not entity.length:
        raise cherrypy.HTTPError(411)

    with cherrypy.HTTPError.handle(ValueError, 400, 'Invalid JSON Document'):
        cherrypy.serving.request.json = json.loads(entity.fp.read().decode('utf-8'))


def json_error_output(status, message, traceback, version):

    status = status.split(' ')[0]
    status = int(status)

    response = cherrypy.response
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({'status': status, 'message': message, 'traceback': traceback, 'version': version})

