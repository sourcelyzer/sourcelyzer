from sourcelyzer.properties import load_from_file
from sourcelyzer.cli import outnl, ask_yesno, ask_generic
from sourcelyzer.dao import Base, User, Settings, PluginRepository
from sourcelyzer.utils import hashing as hashutils

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os, sys

def install(arguments):

    intro_msg = """
===============================================================================
= Sourcelyzer Installation                                                    =
===============================================================================

Welcome to Sourcelyzer.

This tool will install your database, create the admin account, and generate
any necessary secret tokens.

    """

    outnl(intro_msg)

    while True:
        conffile = ask_generic('Location of your configuration file:', './conf/server.properties')
        if os.path.exists(conffile) == False:
            print('Unable to find %s' % conffile)
            continue
        else:
            break

    outnl('Loading configuration...')
    props = load_from_file(conffile)

    outnl('Testing database...')
    engine = create_engine(props['sourcelyzer.db.uri'])
    connection = engine.connect()

    tables = Base.metadata.tables.keys()
    tables_to_install = 0
    total_tables = len(tables)

    for table in tables:
        if engine.dialect.has_table(connection, table) == False:
            tables_to_install += 1

    reinstall = False
    install = False

    if tables_to_install == 0:
        outnl('The database appears to already be installed.')
        reinstall = ask_yesno('Would you like to reinstall the database?', False)

    elif tables_to_install == total_tables:
        install = True
    else:
        outnl('the database appears to be incorrectly installed.')
        reinstall = ask_yesno('Would you like to reinstall the database?', False)

    if reinstall == True:
        reinstall = ask_yesno('This will delete any existing data. ARE YOU SURE?', False)
        if reinstall == True:
            install = True

    if install == False:
        return

    outnl('Deleting existing database')
    Base.metadata.drop_all(engine)

    outnl('Installing database')
    Base.metadata.create_all(engine)

    admin_user = ask_generic('Admin username:', 'admin')
    admin_password = ask_generic('Admin password:', 'admin')
    admin_email = ask_generic('Admin email:', 'admin@admin.com')

    outnl('Creating admin user')
    Session = sessionmaker(bind=engine)
    session = Session()

    admin_dao = User(username=admin_user, password=hashutils.gen_passwd_hash(admin_password), email=admin_email, is_admin=True)
    session.add(admin_dao)

    outnl('Creating secrets')
    secret_bytes = os.urandom(256)
    setting_dao = Settings(setting_name='sourcelyzer.app.secret', setting_value=secret_bytes)
    secret_bytes = os.urandom(256)
    setting_dao = Settings(setting_name='sourcelyzer.digest.secret', setting_value=secret_bytes)
    session.add(setting_dao)

    outnl('Initializing Plugins')

    session.add(PluginRepository(name='Sourcelyzer Plugin Repository', url='https://raw.githubusercontent.com/sourcelyzer/slpr/develop/repo'))

    outnl('Committing changes')
    session.commit()

    outnl('Installation complete!')

