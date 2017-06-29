import cherrypy
from cherrypy.process import wspbus, plugins
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

class SAPlugin(plugins.SimplePlugin):
    def __init__(self, bus, dburi):
        plugins.SimplePlugin.__init__(self, bus)
        self.dburi = dburi
        self.session = scoped_session(sessionmaker(autoflush=True, autocommit=False))
        self.engine = None

    def start(self):
        self.bus.log('Starting DB Session')
        self.engine = create_engine(self.dburi, echo=False)
        self.bus.subscribe('bind-session', self.bind)
        self.bus.subscribe('commit-session', self.commit)


    def stop(self):
        self.bus.log('Stopping DB Session')
        self.bus.unsubscribe('bind-session', self.bind)
        self.bus.unsubscribe('commit-session', self.commit)
        if self.engine:
            self.engine.dispose()
            self.engine = None

    def bind(self):
        self.session.configure(bind=self.engine)
        return self.session

    def commit(self):
        try:
            self.session.commit()
        except:
            self.session.rollback()
        finally:
            self.session.remove()


