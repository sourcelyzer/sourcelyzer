import cherrypy
from cherrypy.process import wspbus, plugins
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

class SATool(cherrypy.Tool):
    def __init__(self, dburi):
        cherrypy.Tool.__init__(self, 'on_start_resource', self.bind_session, priority=10)
        self.dburi = dburi
        self.engine = create_engine(self.dburi)
        self.session = scoped_session(sessionmaker(bind=self.engine))

    def _setup(self):
        cherrypy.Tool._setup(self)
        cherrypy.request.hooks.attach('on_end_resource', self.commit_transaction, priority=80)

    def bind_session(self):
#        session = cherrypy.engine.publish('bind-session').pop()
        cherrypy.request.db = self.session()

    def commit_transaction(self):
        if not hasattr(cherrypy.request, 'db'):
            return
        try:
            cherrypy.request.db.commit()
        finally:
            cherrypy.request.db.close()

        cherrypy.request.db = None
        cherrypy.engine.publish('commit-transaction')


