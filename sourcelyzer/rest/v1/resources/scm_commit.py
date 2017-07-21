from sourcelyzer.dao import ScmCommit
from sourcelyzer.rest.v1.resources.base import DBResource
from sourcelyzer.rest.tools import RequireAuthentication
import cherrypy

class ScmCommitResource(DBResource):
    resource = ScmCommit
 
