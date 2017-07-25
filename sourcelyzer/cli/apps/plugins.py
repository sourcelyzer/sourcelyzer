import os
import pickle
import hashlib
import io
import json
import zipfile
import shutil
import tempfile
import threading
import configparser
import logging
from datetime import datetime

from colorama import Fore
from docopt import docopt
from sourcelyzer.properties import load_from_file
from sourcelyzer.dao import PluginRepository
from sourcelyzer.logging import init_logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sourcelyzer.plugins.key import PluginKey
from sourcelyzer.exceptions import *
from sourcelyzer.utils.hashing import verify_md5sum_string, verify_sha256sum_string
from sourcelyzer.utils.hashing import verify_md5sum_stream, verify_sha256sum_stream
import requests
from requests.exceptions import HTTPError, ConnectionError

__doc__ = """Sourcelyzer Plugin Installer

This is an internal CLI script and is not meant to be used .

Usage:
    plugins.py install -k <plugin_key> -s <sessionid> -a <authtoken> [-c <config_file>] [-d] [-n] 
    plugins.py uninstall -k <plugin_key> -s <sessionid> -a <authtoken> [-c <config_file>] [-d] [-n]

Commands:
    install         Install a plugin
    uninstall       Remove a plugin

Options:
    -k --key PLUGIN_KEY        Plugin key
    -s --sessionid SESSION_ID  Session ID
    -a --auth AUTH_TOKEN       Authorization token
    -c --config CONFIG_FILE    Location of sourcelyzer configuration file
    -d --debug                 Debug output
    -f --force                 If plugin exists, overwrite it
    -n --no-color                 Turn off colored output
"""

LOGLVL_COLORMAP = {
    'DEBUG': Fore.CYAN,
    'INFO': Fore.GREEN,
    'WARNING': Fore.YELLOW,
    'ERROR': Fore.RED,
    'CRITICAL': Fore.MAGENTA
}


class InstallPlugin(threading.Thread):

    def __init__(self, config, session_id, plugin_key,  *args, **kwargs):
        self.config = config
        self.plugin_key = plugin_key

        self.data_dir = os.path.expanduser(self.config['sourcelyzer.data_dir'])
        self.plugin_dir = os.path.join(self.data_dir, 'plugins')
        self.session_dir = os.path.join(self.data_dir, 'sessions')
        self.session_id = session_id

    def run(self, debug=False, colored=False):

        logname = 'sl-install-plugin-%s' % self.ident
        loglvl = logging.DEBUG if debug == True else logging.INFO
        init_logger(logname, loglvl, colored)
        logger = logging.getLogger(logname)

        session_file = os.path.join(self.session_dir, 'session-%s' % self.session_id)

        logger.debug('Data directory: %s' % self.data_dir)
        logger.debug('Plugin directory: %s' % self.plugin_dir)
        logger.debug('Session file: %s' % session_file)

        session_data, session_exp = pickle.load(open(session_file, 'rb'))

        if not os.path.exists(session_file):
            logger.critical('Session file does not exist')
            return

        if session_data['user']['auth'] != True or session_data['user']['token'] != args['--auth']:
            logger.critical('Not Authenticated')
            return

        install_plugin(self.config, self.plugin_key)


def run(args):
    """CLI Run Function.

    Takes output of docopt as input
    """
    loglvl = logging.DEBUG if args['--debug'] == True else logging.INFO

    init_logger('sourcelyzer', loglvl, not args['--no-color'])
    logger = logging.getLogger('sourcelyzer')

    logger.debug(args)

    conffile = args['--config'] if args['--config'] != None else 'conf/server.properties'

    logger.debug('Config file: %s' % conffile)

    config = load_from_file(conffile)

    session_dir = os.path.expanduser(config['sourcelyzer.data_dir'])
    session_dir = os.path.join(session_dir, 'sessions')

    session_file = os.path.join(session_dir, 'session-%s' % args['--sessionid'])

    logger.debug('Session File: %s' % session_file)

    if not os.path.exists(session_file):
        logger.critical('Invalid session')
        return

    session_data, session_exp = pickle.load(open(session_file, 'rb'))

    if session_data['user']['auth'] != True or session_data['user']['token'] != args['--auth']:
        logger.critical('Not Authenticated')
        return

    plugin_key = PluginKey(args['--key'])

    logger.debug('Plugin Key: %s' % str(plugin_key))

    if args['install'] == True:
        install_plugin(config, plugin_key)
    elif args['uninstall'] == True:
        uninstall_plugin(config, plugin_key)


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
    verify_md5sum_string(metadata_content, metadata_md5)

    logger.info('Verifying metadata SHA256')
    metadata_sha     = get_url(metadata_url + '.sha256').text
    verify_sha256sum_string(metadata_content, metadata_sha)

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
        verify_sha256sum_stream(tf, plugin_sha)

        tf.seek(0)
        logger.info('Verifying plugin zip MD5')
        plugin_md5 = get_url(zip_url + '.md5').text
        verify_md5sum_stream(tf, plugin_md5)

        return tf

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
        pass


def search_for_plugin(plugin_key, repos):

    for repo in repos:

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

            repo_url = repo.url
            break

        except (UnknownPluginTypeError, UnknownPluginError, UnknownPluginVersionError):
            pass

    return repo_url

def uninstall_plugin(config, plugin_key, purge=False):

    logger = logging.getLogger('sourcelyzer')
    logger.info('Uninstalling %s' % str(plugin_key))

    target_plugin_dir = os.path.join(config['sourcelyzer.plugin_dir'], '%s.%s' % (plugin_key.plugin_type, plugin_key.plugin_name))

    logger.debug('Target plugin directory: %s' % target_plugin_dir)

    if os.path.exists(target_plugin_dir):
       shutil.rmtree(target_plugin_dir)
    else:
        logger.warning('%s seems to already be uninstalled' % str(plugin_key))

    logger.info('%s uninstalled' % str(plugin_key))

def get_installed_plugin(config, plugin_type, plugin_name):
    plugin_dir = os.path.realpath(config['sourcelyzer.plugin_dir'])
    target_plugin_dir = os.path.join(plugin_dir, '%s.%s' % (plugin_type, plugin_name))

    plugin_conf = configparser.ConfigParser()
    plugin_conf.read(os.path.join(target_plugin_dir, 'plugin.ini'))

    return PluginKey('%s.%s-%s' % (plugin_type, plugin_name, plugin_conf['plugin']['version']))

def is_plugin_installed(config, plugin_type, plugin_name):
    plugin_dir = os.path.realpath(config['sourcelyzer.plugin_dir'])
    target_plugin_dir = os.path.join(plugin_dir, '%s.%s' % (plugin_type, plugin_name))

    return os.path.exists(target_plugin_dir)


def install_plugin(config, plugin_key):
    logger = logging.getLogger('sourcelyzer')
    logger.info('Installing %s' % str(plugin_key))
    exit_code = 0
    try:

        data_dir = os.path.realpath(os.path.expanduser(config['sourcelyzer.data_dir']))
        plugins_dir = os.path.join(data_dir, 'plugins')
        target_plugin_dir = os.path.join(plugins_dir, '%s.%s' % (plugin_key.plugin_type, plugin_key.plugin_name))

        logger.debug('Plugins directory: %s' % plugins_dir)
        logger.debug('Target plugin directory: %s' % target_plugin_dir)

        installed_key = None

        if os.path.exists(target_plugin_dir):

            installed_key = get_installed_plugin(config, plugin_key.plugin_type, plugin_key.plugin_name)
            if installed_key == plugin_key:
                raise PluginAlreadyInstalledError('Plugin %s is already installed' % str(plugin_key))

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

        if is_plugin_installed(config, plugin_key.plugin_type, plugin_key.plugin_name):
            uninstall_plugin(config, plugin_key)

        plugin_url = '%s/%s/%s/%s' % (repo_url, plugin_key.plugin_type, plugin_key.plugin_name, plugin_key.plugin_version)
        plugin_metadata = get_plugin_metadata(plugin_url)
        plugin_zip = get_plugin_zip(plugin_url, target_plugin_dir, plugin_key)

        if installed_key:
            uninstall_plugin(config, installed_key)

        logger.info('Copying temporary zip file to plugin directory')
        dest_zip = os.path.join(target_plugin_dir, '%s.zip' % (str(plugin_key)))

        if not os.path.exists(target_plugin_dir):
            os.makedirs(target_plugin_dir)

        with open(dest_zip, 'wb') as target_f:
            plugin_zip.seek(0)
            while True:
                buf = plugin_zip.read(1024)
                if len(buf) > 0:
                    target_f.write(buf)
                else:
                    break

        plugin_zip.close()

        logger.info('Unzipping plugin')
        with zipfile.ZipFile(dest_zip) as pz:
            pz.extractall(target_plugin_dir)

        logger.info('Plugin %s has been successfully instaled' % str(plugin_key))
    except (UnknownPluginError, UnknownPluginError, UnknownPluginTypeError, UnknownPluginVersionError):
        logger.error('Plugin %s could not be found' % str(plugin_key))
        exit_code = 5
    except PluginAlreadyInstalledError:
        logger.error('Plugin %s is already installed' % str(plugin_key))
        exit_code = 4
    except HTTPError as e:
        logger.error('%s' % e)
        exit_code = 3
    except InvalidHashError as e:
        logger.error('%s' % e)
        exit_code = 2

    return exit_code


if __name__ == '__main__':
    run(docopt(__doc__))

