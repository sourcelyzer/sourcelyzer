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
import sys
import semver
import time
from datetime import datetime
import multiprocessing
import cherrypy

from colorama import Fore
from docopt import docopt
from sourcelyzer.properties import load_from_file
from sourcelyzer.dao import PluginRepository, Plugin
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
    plugins.py install -k <plugin_key> -s <sessionid> -a <authtoken> -r <repoid> [-c <config_file>] [-d] [-n] 
    plugins.py uninstall -k <plugin_key> -s <sessionid> -a <authtoken> [-c <config_file>] [-d] [-n]

Commands:
    install         Install a plugin
    uninstall       Remove a plugin

Options:
    -k --key PLUGIN_KEY        Plugin key
    -r --repo-id REPO_ID       Repository ID
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

    def __init__(self, config, plugin_key, repo_id, task_id, *args, **kwargs):
        self.config = config
        self.plugin_key = plugin_key
        self.repo_id = repo_id
        self.task_id = task_id

        self.data_dir = os.path.realpath(os.path.expanduser(self.config['sourcelyzer.data_dir']))
        self.plugin_dir = os.path.join(self.data_dir, 'plugins')

        threading.Thread.__init__(self, *args, **kwargs)

    def run(self, debug=False, colored=False):

        cherrypy.engine.publish('bg-noise', {
            'state': 'started',
            'msg': 'Starting install of plugin %s' % self.plugin_key,
            'task': self.task_id
        })

        exitcode = 1

        with multiprocessing.Manager() as manager:
            d = manager.dict() 

            p = multiprocessing.Process(target=forked_run, args=(self.config, self.plugin_key, self.repo_id, d))
            p.start()
            pid = p.pid
            cherrypy.engine.publish('bg-noise', {
                'state': 'running',
                'msg': 'Installation running',
                'task': self.task_id,
                'pid': pid
            })
            p.join()

            exitcode = d['exit-code']

        if exitcode == 0:
            r = {
                'state': 'finished',
                'msg': 'Installation of plugin %s is complete' % self.plugin_key,
                'task': self.task_id
            }
        elif exitcode == 1:
            r = {
                'state': 'error',
                'msg': 'The installation failed. Please check the logs',
                'task': self.task_id
            }
        elif exitcode == 2:
            r = {
                'state': 'error',
                'msg': 'One of the repository files was corrupted. Check the logs for more information',
                'task': self.task_id
            }
        elif exitcode == 3:
            r = {
                'state': 'error',
                'msg': 'There was an error communicating with the repository.',
                'task': self.task_id
            }
        elif exitcode == 4:
            r = {
                'state': 'error',
                'msg': 'Plugin is already installed',
                'task': self.task_id
            }
        elif exitcode == 5:
            r = {
                'state': 'error',
                'msg': 'Plugin could not be found',
                'task': self.task_id
            }
        else:
            r = {
                'state': 'error',
                'msg': 'There was no exit code to check.',
                'task': self.task_id
            }

       
        cherrypy.engine.publish('bg-noise', r)


def forked_run(config, plugin_key, repo_id, managed_props):
    """Use with multiprocessing.Process()
    """

    exit_code = install_plugin(config, plugin_key, repo_id)
    managed_props['exit-code'] = exit_code
    return exit_code


def run(args):
    """CLI Run Function.

    Takes output of docopt as input
    """

    exit_code = 0

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
        return 1

    session_data, session_exp = pickle.load(open(session_file, 'rb'))

    if session_data['user']['auth'] != True or session_data['user']['token'] != args['--auth']:
        logger.critical('Not Authenticated')
        return 1

    plugin_key = PluginKey(args['--key'])

    logger.debug('Plugin Key: %s' % str(plugin_key))

    repo_id = int(args['--repo-id'])

    if args['install'] == True:
        exit_code = install_plugin(config, plugin_key, repo_id)
    elif args['uninstall'] == True:
        exit_code = uninstall_plugin(config, plugin_key)

    return exit_code


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

            if plugin_key.plugin_group not in plugins:
                raise UnknownPluginTypeError(plugin_key.plugin_group)

            if plugin_key.plugin_name not in plugins[plugin_key.plugin_group]:
                raise UnknownPluginError(plugin_name)

            if plugin_key.plugin_version not in plugins[plugin_key.plugin_group][plugin_key.plugin_name]['versions']:
                raise UnknownPluginVersionError('%s' % plugin_key)

            repo_url = repo.url
            break

        except (UnknownPluginTypeError, UnknownPluginError, UnknownPluginVersionError):
            pass

    return repo_url

def uninstall_plugin(config, plugin_key, purge=False):

    logger = logging.getLogger('sourcelyzer')
    logger.info('Uninstalling %s' % str(plugin_key))

    data_dir = os.path.realpath(os.path.expanduser(config['sourcelyzer.data_dir']))
    target_plugin_dir = os.path.join(data_dir, 'plugins', '%s.%s' % (plugin_key.plugin_group, plugin_key.plugin_name))

    logger.debug('Target plugin directory: %s' % target_plugin_dir)

    if os.path.exists(target_plugin_dir):
       shutil.rmtree(target_plugin_dir)
    else:
        logger.warning('%s seems to already be uninstalled' % str(plugin_key))

    logger.info('%s uninstalled' % str(plugin_key))

def get_installed_plugin(config, plugin_group, plugin_name):
    logger = logging.getLogger('sourcelyzer')
    data_dir = os.path.realpath(os.path.expanduser(config['sourcelyzer.data_dir']))
    target_plugin_dir = os.path.join(data_dir, 'plugins', '%s.%s' % (plugin_group, plugin_name))

    logger.debug('Checking %s' % target_plugin_dir)

    plugin_conf = configparser.ConfigParser()
    plugin_conf.read(os.path.join(target_plugin_dir, 'plugin.ini'))

    return PluginKey('%s.%s-%s' % (plugin_group, plugin_name, plugin_conf['plugin']['version']))

def is_plugin_installed(config, plugin_group, plugin_name):
    data_dir = os.path.realpath(os.path.expanduser(config['sourcelyzer.data_dir']))
    target_plugin_dir = os.path.join(data_dir, 'plugins', '%s.%s' % (plugin_group, plugin_name))

    return os.path.exists(target_plugin_dir)

def check_for_installed_plugin(data_dir, plugin_key):
    plugin_dir = os.path.join(data_dir, 'plugins', '%s.%s' % (plugin_key[0], plugin_key[1]))

    if os.path.exists(plugin_dir):
        config = configparser.ConfigParser()
        config.read(os.path.join(plugin_dir, 'plugin.ini'))

        return PluginKey('%s.%s-%s' % (plugin_conf['plugin']['group'], plugin_conf['plugin']['name'], plugin_conf['version']))
    else:
        return None

def install_plugin(config, plugin_key, repo_id):

    plugin_key = PluginKey(str(plugin_key))

    logger = logging.getLogger('sourcelyzer')
    logger.info('Installing %s' % str(plugin_key))
    exit_code = 0
    upgrade = False
    downgrade = False
    try:

        data_dir = os.path.realpath(os.path.expanduser(config['sourcelyzer.data_dir']))
        plugins_dir = os.path.join(data_dir, 'plugins')
        target_plugin_dir = os.path.join(plugins_dir, '%s.%s' % (plugin_key.plugin_group, plugin_key.plugin_name))

        logger.debug('Plugins directory: %s' % plugins_dir)
        logger.debug('Target plugin directory: %s' % target_plugin_dir)

        installed_key = None

        if os.path.exists(target_plugin_dir):

            installed_key = get_installed_plugin(config, plugin_key.plugin_group, plugin_key.plugin_name)
            if installed_key == plugin_key:
                raise PluginAlreadyInstalledError('Plugin %s is already installed' % str(plugin_key))
            elif semver.compare(installed_key[2], plugin_key[2]) == -1:
                logger.warning('Downgraining from %s to %s' % (installed_key, plugin_key))
                downgrade = True
            elif semver.compare(installed_key[2], plugin_key[2]) == 1:
                logger.warning('Upgrading from %s to %s' % (plugin_key, installed_key))
                upgrade = True
            
        engine = create_engine(config['sourcelyzer.db.uri'])

        Session = sessionmaker(bind=engine)
        session = Session()

        repo = session.query(PluginRepository).filter(PluginRepository.id == repo_id).first()

        try:

            logger.info('Checking repository %s' % repo.url)
            try:
                plugins = get_url(repo.url + '/plugins.json').json()
            except (ConnectionError, HTTPError) as e:
                logger.warning('%s' % e)

            if plugin_key.plugin_group not in plugins:
                raise UnknownPluginTypeError(plugin_key.plugin_group)

            if plugin_key.plugin_name not in plugins[plugin_key.plugin_group]:
                raise UnknownPluginError(plugin_key.plugin_name)

            if plugin_key.plugin_version not in plugins[plugin_key.plugin_group][plugin_key.plugin_name]['versions']:
                raise UnknownPluginVersionError('%s' % plugin_key)

            logger.info('Match!')
            repo_url = repo.url

        finally:
            session.close()


        if not repo_url:
            raise UnknownPlugin('%s' % plugin_key)

        if is_plugin_installed(config, plugin_key.plugin_group, plugin_key.plugin_name):
            uninstall_plugin(config, plugin_key)

        plugin_url = '%s/%s/%s/%s' % (repo_url, plugin_key.plugin_group, plugin_key.plugin_name, plugin_key.plugin_version)
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

        logger.info('Creating database record')

        if upgrade == True or downgrade == True:
            plugin = session.query(Plugin).filter(Plugin.key == str(installed_key)).first()
            if not plugin:
                logger.warning('Expected to find plugin in database for upgrade/downgrade: %s' % str(plugin_key))
                plugin = Plugin()
        else:
            plugin = Plugin()


        plugin.name = plugin_key.plugin_name
        plugin.group = plugin_key.plugin_group
        plugin.version = plugin_key.plugin_version
        plugin.key = str(plugin_key)
        plugin.installed = True
        plugin.enabled = True

        
        if upgrade == False and downgrade == False:
            session.add(plugin)

        session.commit()

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
    except Exception as e:
        logger.critical('Unhandled Exception')
        logger.critical(type(e).__name__ + ': ' + e.message)
        logger.exception(e)
        exit_code = 1

    return exit_code


if __name__ == '__main__':
    sys.exit(run(docopt(__doc__)))

