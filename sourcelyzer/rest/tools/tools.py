import cherrypy
from sourcelyzer.rest.utils.auth import verify_auth_token

def check_authentication(session, auth_token):
    if 'user' not in session:
        raise cherrypy.HTTPError(401)

    print('check authentication for user %s' % session['user'].username)

    if not auth_token:
        raise cherrypy.HTTPError(401)


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
        check_authentication(cherrypy.session, cherrypy.request.headers.get('Authorization', None))
        return f(*args, **kwargs)

    return wrapper

