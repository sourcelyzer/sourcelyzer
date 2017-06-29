from docopt import docopt
from sourcelyzer.app import App
from sourcelyzer.properties import load_properties
import sys
import os
import cherrypy

def ask_generic(msg,default=None,valids=None):

    msg = '[x] %s' % msg

    if default != None:
        msg += ' (%s): ' % default

    while True:
        sys.stdout.write(msg)
        sys.stdout.flush()
        user_input = sys.stdin.readline().strip()
        if valids != None and user_input not in valids:
            continue
        elif user_input == "" and default == None:
            continue
        else:
            break

    if user_input == "" and default != None:
        user_input = default

    return user_input



def ask_yesno(msg,default=True):

    valids = ['Y','y','n','N']

    yn = 'Y/n' if default == True else 'y/N'

    while True:
        sys.stdout.write('[x] %s [%s]: ' % (msg, yn))
        sys.stdout.flush()
        user_input = sys.stdin.readline().strip()

        if user_input == "":
            user_input = 'Y' if default == True else 'N'

        if user_input not in valids:
            continue
        else:
            break;
    
    if user_input == 'Y' or user_input == 'y':
        return True
    else:
        return False


def install(arguments):

    intro_msg = """
===============================================================================
= Sourcelyzer Installation                                                    =
===============================================================================

Welcome to Sourcelyzer. The following steps will install Sourcelyzer for you.

    """

    print(intro_msg)

    continue_installation = True

    while True:
        conffile = ask_generic('Location of your configuration file:', './conf/server.properties')
        if os.path.exists(conffile) == False:
            print('Unable to find %s' % conffile)
            continue
        else:
            break;

    print('Loading configuration...')

    from sourcelyzer.properties import load_properties
    props = load_properties(conffile)

    print('Testing database...')
    from sourcelyzer.dao import Base, User, Settings
    from sourcelyzer.utils.pw import gen_pass_hash
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(props['sourcelyzer.db.uri'])
    connection = engine.connect()

    tables = Base.metadata.tables.keys()
    tables_to_install = 0
    total_tables = len(tables)

    for table in tables:
        if engine.dialect.has_table(connection, table) == False:
            tables_to_install += 1

    reinstall = False
    
    if tables_to_install == 0:
        print('The database appears to already be setup.')
        reinstall = ask_yesno('Would you like to reinstall the database?', False)
    elif tables_to_install == total_tables:
        reinstall = True
    else:
        print('The database appears to be incorrectly installed.')
        reinstall = ask_yesno('Would you like to reinstall the database?', False)

    if reinstall == False:
        print('Stopping the installation.')
        return

    print('Deleting existing database')
    Base.metadata.drop_all(engine)
    
    print('Creating database')
    Base.metadata.create_all(engine)

    admin_user = ask_generic('Admin username:','admin')
    admin_password = ask_generic('Admin password:','admin')
    admin_email = ask_generic('Admin email:','admin@admin.com')

    print('Creating admin user')
    Session = sessionmaker(bind=engine)
    session = Session()

    admin_dao = User(username=admin_user, password=gen_pass_hash(admin_password.encode('utf8')), email=admin_email, is_admin=True)
    session.add(admin_dao)
   
    session.commit()

    print('Creating unique secret')
    secret_bytes = os.urandom(256)

    setting_dao = Settings(setting_name='sourcelyzer.secret', setting_value=secret_bytes)
    session.add(setting_dao)
    session.commit()

    print('-----------------------')
    print('Installation Complete!')

class HelloWorld():
    @cherrypy.expose
    def index(self):
        return "Hello World!"


def start_console(arguments):

    cherrypy.config.update(arguments['--config'])
    cherrypy.quickstart(HelloWorld(), '/', arguments['--config'])


def run(command, cli_args, doc):
    arguments = docopt(doc, version='Sourcelyzer 0.0.1', argv=cli_args)

    if 'start-console' in arguments and arguments['start-console']:
        command = 'start-console'

    if command == 'install':
        install(arguments)
    elif command == 'start-console':
        start_console(arguments)
    else:
        print(arguments)


