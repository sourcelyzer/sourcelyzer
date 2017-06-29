import cherrypy
from sourcelyzer.rest.utils import check_auth_token


def RequiredParam(paramName):
    def decorator(f):
        def wrapper(*args, **kwargs):
            if paramName not in cherrypy.request.params:
                raise cherrypy.HTTPError(400, 'Missing parameter %s' % paramName)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def RequireAuthentication(f):
    def wrapper(*args, **kwargs):
        if 'user' not in cherrypy.session:
            raise cherrypy.HTTPError(401)

        if 'secret' not in cherrypy.session['user']:
            raise cherrypy.HTTPError(401)

        if not cherrypy.session['user']['secret']:
            raise cherrypy.HTTPError(401)

        if not 'Authorization' in cherrypy.request.headers:
            raise cherrypy.HTTPError(401)

        secret = cherrypy.session['user']['secret']
        token = cherrypy.request.headers.get('Authorization')

        if not check_auth_token(token, secret, cherrypy.session.id.encode('utf-8')):
            raise cherrypy.HTTPError(401)

        return f(*args, **kwargs)

    return wrapper

