from sourcelyzer.cli import outnl
from sourcelyzer.properties import load_from_file
from sourcelyzer.app import App
import cherrypy

def init_server(properties):
    cherrypy.config.update({
        'server.socket_host': properties['sourcelyzer.server.listen_addr'],
        'server.socket_port': int(properties['sourcelyzer.server.listen_port'])
    })

    cherrypy.tree.mount(Root(), '/')

def start(arguments, properties):
    outnl('start server')

def stop(arguments, properties):
    outnl('stop server')

def restart(arguments, properties):
    stop()
    start()

def start_console(arguments, properties):

    app = App(properties)
    app.run()

def server(arguments):

    conffile = arguments['--config'] if arguments['--config'] != None else 'conf/server.properties'

    props = load_from_file(conffile)

    if arguments['start']:
        start(arguments, props)
    elif arguments['stop']:
        stop(arguments, props)
    elif arguments['restart']:
        restart(arguments, props)
    elif arguments['start-console']:
        start_console(arguments, props)
    else:
        outnl('Wait, something is amiss. Some how there is an invalid command')

