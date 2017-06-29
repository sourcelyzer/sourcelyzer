import cherrypy
import simplejson as json
from sourcelyzer.rest.v1.exceptions import RestResourceException
from sourcelyzer.rest.tools import RequireAuthentication

def json_processor(entity):
    print('custom json parser - entity.length: %s' % entity.length)
    if entity.length == 0 or entity.length == '0':
        print('HOW ARE YOU NOT HERE?!')
        cherrypy.serving.request.json = None
        return

    if not entity.length:
        raise cherrypy.HTTPError(411)

    with cherrypy.HTTPError.handle(ValueError, 400, 'Invalid JSON Document'):
        cherrypy.serving.request.json = json.loads(entity.fp.read().decode('utf-8'))


def json_error_output(status, message, traceback, version):
    """
    Formats cherrypy errors into JSON
    """
    response = cherrypy.response
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({'status': status, 'message': message, 'traceback': traceback, 'version': version})

class RESTResource():
    """
    Base REST Resource class

    Handles routing of HTTP verbs and some basic error handling
    """
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def default(self, *vpath, **params):
        method = getattr(self, 'handle_%s' % cherrypy.request.method, None)
        if not method:
            methods = [x.replace('handle_', '') for x in dir(self) if x.startswith('handle_')]
            cherrypy.response.headers['Allow'] = ','.join(methods)
            raise cherrypy.HTTPError(405)
        return method(*vpath, **params)

@cherrypy.popargs('resid')
class DBResource(RESTResource):
    """
    Base class for database resources
    """
    resource = None
    skipfields = ['id', 'last_modified', 'created_on']

    def __init__(self):
        if self.resource == None:
            raise RestResourceException('A DB REST Resource needs a DB object')

    @RequireAuthentication
    def handle_GET(self, resid=None, *vpath, **params):
        session = cherrypy.request.db

        output = None

        if resid == None:
            output = []
            resources = session.query(self.resource).all()
            for resource in resources:
                output.append(resource.toDict())
        else:
            try:
                resid = int(resid)
            except ValueError:
                raise cherrypy.HTTPError(404, 'Project id %s does not exist' % resid)

            resource = session.query(self.resource).filter(self.resource.id == resid).first()

            if resource:
                output = resource.toDict()
            else:
                raise cherrypy.HTTPError(404, 'Project id %s does not exist' % resid)
        
        return output

    
    @RequireAuthentication
    def handle_PUT(self, resid, *vpath, **params):
        session = cherrypy.request.db

        the_input = cherrypy.request.json

        resource = session.query(self.resource).filter(self.resource.id == int(resid)).first()

        if resource == None:
            session.close()
            raise cherrypy.HTTPError(404)
        
        for c in self.resource.__table__.columns:
            colname = str(c).split('.')[-1]
            if colname in self.skipfields:
                continue

            if colname not in the_input:
                session.close()
                raise cherrypy.HTTPError(400, 'Missing field: %s' % colname)
            
            setattr(resource, colname, the_input[colname])

        session.commit()

        output = self.handle_GET(resid=resource.id)
        session.close()
        return output

    @RequireAuthentication
    def handle_POST(self, *vpath, **params):

        session = cherrypy.request.db
        the_input = cherrypy.request.json

        if 'id' in the_input:
            raise cherrypy.HTTPError(400, 'ID can not be part of the input')

        resource = self.resource()

        for c in self.resource.__table__.columns:
            colname = str(c).split('.')[-1]
            if colname in self.skipfields:
                continue

            if colname not in the_input:
                raise cherrypy.HTTPError(400, 'Missing field: %s' % colname)

            setattr(resource, colname, the_input[colname])

        session.add(resource)
        session.commit()

        output = self.handle_GET(resid=resource.id)
        
        session.close()
        return output


