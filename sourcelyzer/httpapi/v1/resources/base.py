import cherrypy
import simplejson as json

from sourcelyzer.httpapi.tools import RequireAuthentication
from sourcelyzer.utils.hashing import gen_passwd_hash

class RESTResource():
    """A basic REST Resource

    REST may be a misnomer but you'll get over it.
    Automatically directs requests to methods that are named handle_[HTTP_METHOD].

    eg: def handle_POST(self):
            print('post')

    If the method does not exist, then a 405 is raised
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

@cherrypy.popargs('resource_id')
class DBResource(RESTResource):
    """A basic DB REST Resource

    Sets up POST, PUT, DELETE, and GET methods for a
    sqlalchemy orm object.
    """

    resource = None
    skipfields = ['id', 'last_modified', 'created_on']

    def handle_GET(self, resource_id=None, *vpath, **params):
        session = cherrypy.request.db

        output = None

        if resource_id == None:
            output = []
            resources = session.query(self.resource).all()
            for resource in resources:
                output.append(resource.toDict())
        else:
            try:
                resource_id = int(resource_id)
            except ValueError:
                raise cherrypy.HTTPError(400, 'Invalid resource id: %s' % resource_id)

            resource = session.query(self.resource).filter(self.resource.id == resource_id).first()

            if resource:
                output = resource.toDict()
            else:
                raise cherrypy.HTTPError(404, 'Resource id %s does not exist' % resource_id)

        return output


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

            if colname not in the_input and colname not in self.skipfields:
                raise cherrypy.HTTPError(400, 'Missing field: %s' % colname)

            if colname in the_input:
                setattr(resource, colname, the_input[colname])

        session.add(resource)
        session.commit()

        output = self.handle_GET(resource_id=resource.id)

        return output

    def handle_DELETE(self, resource_id, *vpath, **params):
        session = cherrypy.request.db

        resource = session.query(self.resource).filter(self.resource.id == resource_id).first()

        if resource == None:
            raise cherrypy.HTTPError(404, 'ID not found: %s' % resource_id)
        session.delete(resource)
        session.commit()

        return {'ok': True}

    def handle_PUT(self, resource_id, *vpath, **params):
        session = cherrypy.request.db
        the_input = cherrypy.request.json

        resource = session.query(self.resource).filter(self.resource.id == resource_id).first()

        if resource == None:
            raise cherrypy.HTTPError(404, 'ID not found: %s' % resource_id)

        for c in self.resource.__table__.columns:
            colname = str(c).split('.')[-1]

            if colname in the_input:
                setattr(resource, colname, the_input[colname])

#        session.save(resource)
        session.commit()

        output = self.handle_GET(resource_id=resource.id)

        return output


class SecureWriteDBResource(DBResource):

    @RequireAuthentication
    def handle_POST(self, *vpath, **params):
        DBResource.handle_POST(self, *vpath, **params)

class SecureReadDBResource(DBResource):

    @RequireAuthentication
    def handle_GET(self, *vpath, **params):
        DBResource.handle_GET(self, *vpath, **params)

class SecureDBResource(DBResource):

    @RequireAuthentication
    def handle_GET(self, *vpath, **params):
        DBResource.handle_GET(self, *vpath, **params)

    @RequireAuthentication
    def handle_POST(self, *vpath, **params):
        DBResource.handle_POST(self, *vpath, **params)

