from sourcelyzer.dao import ScmCommit
from sourcelyzer.httpapi.v1.resources.base import DBResource
from sourcelyzer.httpapi.tools import RequireAuthentication
import cherrypy

class ScmCommitResource(DBResource):
    resource = ScmCommit
 
