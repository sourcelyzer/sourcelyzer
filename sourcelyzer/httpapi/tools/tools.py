import cherrypy
from sourcelyzer.httpapi.utils.auth import verify_auth_token

def check_required_param(paramName, params):
    if paramName not in params:
        raise cherrypy.HTTPError(400, 'Missing parameter %s' % paramName)


def RequiredParam(paramName):
    def decorator(f):
        def wrapper(*args, **kwargs):
            check_required_param(paramName, cherrypy.request.params)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def RequireAuthentication(f):
    def wrapper(*args, **kwargs):

        if 'user' not in cherrypy.session:
            raise cherrypy.HTTPError(401)

        if not cherrypy.session['user']['auth']:
            raise cherrypy.HTTPError(401)

        if 'token' not in cherrypy.session['user']:
            raise cherrypy.HTTPError(401)

        auth_token = cherrypy.request.headers.get('Authorization', None)

        if auth_token != cherrypy.session['user']['token']:
            raise cherrypy.HTTPError(401)

        return f(*args, **kwargs)

    return wrapper

