from sourcelyzer.dao import Project
from sourcelyzer.rest.v1.base import DBResource
from sourcelyzer.rest.tools import RequireAuthentication
import cherrypy

class ProjectResource(DBResource):
    resource = Project

    @RequireAuthentication
    def handle_GET(self, resid=None, *vpath, **params):
        if 'key' in params:
            return self._get_project_by_key(params['key'])
        else:
            return DBResource.handle_GET(self, resid, *vpath, **params)

    def _get_project_by_key(self, projectKey):
        session = cherrypy.request.db

        resource = session.query(self.resource).filter(self.resource.key == projectKey).first()
       
        if resource:
            return resource.toDict()
        else:
            raise cherrypy.HTTPError(404, 'Project key %s does not exist' % projectKey)

