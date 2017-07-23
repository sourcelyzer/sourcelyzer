import os
import pickle
import requests
from docopt import docopt
from sourcelyzer.properties import load_from_file
from sourcelyzer.dao import PluginRepository
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sourcelyzer.utils.crypto import file_hash
from sourcelyzer.plugins.key import PluginKey
import hashlib
import io
import json
import zipfile
import configparser
import shutil
import tempfile
import threading
import logging
from datetime import datetime
from colorama import Fore
import http.client
from requests.exceptions import HTTPError, ConnectionError

__doc__ = """Sourcelyzer Plugin Installer

This is an internal CLI script and is not meant to be used .

Usage:
    sl-install.py install --key=<plugin_key> --sessionid=<sessionid> --auth=<authtoken> [--config=<config_file>] [--debug] [--no-color]

Commands:
    install         Install a plugin
    uninstall       Remove a plugin

Options:
    -k --key PLUGIN_KEY        Plugin key
    -s --sessionid SESSION_ID  Session ID
    -a --auth AUTH_TOKEN       Authorization token
    -c --config CONFIG_FILE    Location of sourcelyzer configuration file
    -d --debug                 Debug output
    --no-color                 Turn off colored output
"""

LOGLVL_COLORMAP = {
    'DEBUG': Fore.CYAN,
    'INFO': Fore.GREEN,
    'WARNING': Fore.YELLOW,
    'ERROR': Fore.RED,
    'CRITICAL': Fore.MAGENTA
}

MSG_COLORMAP = {
    'DEBUG': Fore.LIGHTGREEN_EX,
    'INFO': Fore.RESET,
    'WARNING': Fore.LIGHTWHITE_EX,
    'ERROR': Fore.LIGHTRED_EX,
    'CRITICAL': Fore.LIGHTMAGENTA_EX
}

class StandardLogFormatter(logging.Formatter):
    def format(self, record):
        msg = '%s [%s] %s: %s' % (datetime.now(), record.levelname.ljust(8), record.name, record.msg)
        return msg


class ColorLogFormatter(logging.Formatter):

    def format(self, record):
        lvlname_color = LOGLVL_COLORMAP[record.levelname]
        msg_color = MSG_COLORMAP[record.levelname]
        lvlname = record.levelname.ljust(8)

        lvl = '%s%s [%s%s%s] %s%s: %s' % (Fore.WHITE, datetime.now(), lvlname_color, lvlname, Fore.WHITE, Fore.BLUE, record.name, Fore.RESET)

        msg = '%s %s%s%s' % (lvl, msg_color, record.msg, Fore.RESET)
        return msg

def init_logging(name, level, color=True):

    formatter = ColorLogFormatter() if color == True else StandardLogFormatter()

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = True


class InstallPlugin(threading.Thread):

    def __init__(self, config, session, plugin_key,  *args, **kwargs):
        self.config = config
        self.session = session
        self.plugin_key = plugin_key

    def run(self):
        install_plugin(config, plugin_key)



def run(args):

    loglvl = logging.DEBUG if args['--debug'] == True else logging.INFO

    init_logging('sourcelyzer', loglvl, not args['--no-color'])
    logger = logging.getLogger('sourcelyzer')

    cwd = os.path.realpath(os.path.join(os.path.dirname(__file__), '../', '../', '../'))

    logger.debug('Current Working Directory: %s' % cwd)

    os.chdir(cwd)

    conffile = args['--config'] if args['--config'] != None else 'conf/server.properties'

    logger.debug('Config file: %s' % conffile)

    config = load_from_file(conffile)

    session_dir = os.path.expanduser('~/.sourcelyzer')
    session_dir = os.path.join(session_dir, 'sessions')

    session_file = os.path.join(session_dir, 'session-%s' % args['--sessionid'])

    logger.debug('Session File: %s' % session_file)

    session_data, session_exp = pickle.load(open(session_file, 'rb'))

    if session_data['user']['auth'] != True or session_data['user']['token'] != args['--auth']:
        raise Exception('Not Authenticated')

    plugin_key = PluginKey(args['--key'])

    logger.debug('Plugin Key: %s' % str(plugin_key))

    install_plugin(config, plugin_key)


class InvalidHashError(BaseException):
    pass

class UnknownPluginError(BaseException):
    pass

class UnknownPluginTypeError(BaseException):
    pass

class UnknownPluginError(BaseException):
    pass

class UnknownPluginVersionError(BaseException):
    pass

class PluginAlreadyInstalledError(BaseException):
    pass

def verify_hash_str(content, target_hash, hasher):
    verify_hash_fobj(io.BytesIO(content.encode('utf-8')), target_hash, hasher)

def verify_hash_fobj(fobj, target_hash, hasher):
    check_hash = file_hash(fobj, hasher)

    if check_hash != target_hash:
        raise InvalidHashError('Expected %s but got %s' % (target_hash, check_hash))

def get_url(url, stream=False):
    logger = logging.getLogger('sourcelyzer')
    logger.debug('GET %s' % url)

    r = requests.get(url, stream=stream)
    r.raise_for_status()
    return r

def get_plugin_metadata(plugin_url):

    logger = logging.getLogger('sourcelyzer')
    logger.info('Fetching plugin metadata')

    metadata_url = plugin_url + '/metadata.json'

    metadata_content = get_url(metadata_url).text

    logger.info('Verifying metadata MD5')
    metadata_md5     = get_url(metadata_url + '.md5').text
    verify_hash_str(metadata_content, metadata_md5, hashlib.md5())

    logger.info('Verifying metadata SHA256')
    metadata_sha     = get_url(metadata_url + '.sha256').text
    verify_hash_str(metadata_content, metadata_sha, hashlib.sha256())

    logger.info('Loading metadata')
    plugin_metadata = json.loads(metadata_content)

    return plugin_metadata


def get_plugin_zip(plugin_url, plugin_dir, plugin_key):
    zip_url = '%s/%s.zip' % (plugin_url, plugin_key)
    logger = logging.getLogger('sourcelyzer')
    logger.info('Downloading plugin zip')

    r = get_url(zip_url, stream=True)
    tf = tempfile.TemporaryFile('wb+')

    try:
        for chunk in r:
            tf.write(chunk)
        tf.seek(0)

        logger.info('Verifying plugin zip SHA256')
        plugin_sha = get_url(zip_url + '.sha256').text
        verify_hash_fobj(tf, plugin_sha, hashlib.sha256())

        tf.seek(0)
        logger.info('Verifying plugin zip MD5')
        plugin_md5 = get_url(zip_url + '.md5').text
        verify_hash_fobj(tf, plugin_md5, hashlib.md5())
 

        dest_zip = os.path.join(plugin_dir, '%s.zip' % str(plugin_key))

        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)

        logger.info('Copying temporary zip file to target directory')
        with open(dest_zip, 'wb') as target_f:
            tf.seek(0)

            while True:
                buf = tf.read(1024)
                if len(buf) > 0:
                    target_f.write(buf)
                else:
                    break
        return dest_zip

    finally:
        tf.close()


def install_plugin(config, plugin_key):
    logger = logging.getLogger('sourcelyzer')
    logger.info('Attempting to install %s' % str(plugin_key))

    try:

        plugins_dir = os.path.realpath(config['sourcelyzer.plugin_dir'])
        target_plugin_dir = os.path.join(plugins_dir, '%s.%s' % (plugin_key.plugin_type, plugin_key.plugin_name))

        logger.debug('Plugins directory: %s' % plugins_dir)
        logger.debug('Target plugin directiry: %s' % target_plugin_dir)

        plugin_ini = os.path.join(target_plugin_dir, 'plugin.ini')
        backup_dir = os.path.join(plugins_dir, 'backups')

        if os.path.exists(target_plugin_dir):
            logger.debug('Target plugin directory exists')

            plugin_conf = configparser.ConfigParser()
            plugin_conf.read(plugin_ini)

            if plugin_conf['plugin']['version'] == plugin_key.plugin_version:
                raise PluginAlreadyInstalledError('Plugin %s is already installed' % str(plugin_key))
            else:
                logger.info('Plugin already installed but versions differ. Backing up currently installed plugin.')
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)

                shutil.copytree(target_plugin_dir, os.path.join(plugins_dir, 'backups', '%s.%s' % (plugin_key.plugin_type, plugin_key.plugin_name)))

        engine = create_engine(config['sourcelyzer.db.uri'])

        Session = sessionmaker(bind=engine)
        session = Session()

        records = session.query(PluginRepository).all()

        repo_url = None

        for repo in records:

            try:

                logger.info('Checking repository %s' % repo.url)
                try:
                    plugins = get_url(repo.url + '/plugins.json').json()
                except (ConnectionError, HTTPError) as e:
                    logger.warning('%s' % e)
                    continue

                if plugin_key.plugin_type not in plugins:
                    raise UnknownPluginTypeError(plugin_key.plugin_type)

                if plugin_key.plugin_name not in plugins[plugin_key.plugin_type]:
                    raise UnknownPluginError(plugin_name)

                if plugin_key.plugin_version not in plugins[plugin_key.plugin_type][plugin_key.plugin_name]['versions']:
                    raise UnknownPluginVersionError('%s' % plugin_key)

                logger.info('Match!')
                repo_url = repo.url
                break

            except (UnknownPluginTypeError, UnknownPluginError, UnknownPluginVersionError):
                pass

        session.close()


        if not repo_url:
            raise UnknownPlugin('%s' % plugin_key)

        plugin_url = '%s/%s/%s/%s' % (repo_url, plugin_key.plugin_type, plugin_key.plugin_name, plugin_key.plugin_version)
        plugin_metadata = get_plugin_metadata(plugin_url)
        plugin_zip = get_plugin_zip(plugin_url, target_plugin_dir, plugin_key)

        with zipfile.ZipFile(plugin_zip) as pz:
            pz.extractall(target_plugin_dir)
    except (UnknownPluginError, UnknownPluginError, UnknownPluginTypeError, UnknownPluginVersionError):
        logger.error('Plugin %s could not be found' % str(plugin_key))
    except PluginAlreadyInstalledError:
        logger.error('Plugin %s is already installed' % str(plugin_key))
    except HTTPError as e:
        logger.error('%s' % e)
    except InvalidHashError as e:
        logger.error('%s' % e)
    except Exception as e:
        logger.critical('Unknown Exception')
        logger.exception(e)


if __name__ == '__main__':
    run(docopt(__doc__))

