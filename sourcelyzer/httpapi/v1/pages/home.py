import cherrypy

class HomePage():
    @cherrypy.expose
    def index(self):
        return 'Hi'

