import requests
from io import BytesIO

def parse_zip_filename(fn):

    t, nv, ext = fn.split('.')

    n = '-'.join(nv.split('-')[:-1])
    v = nv.split('-')[-1:]

    return (t,n,v)


class Plugin():
    def __init__(self, plugin_type, plugin_name, plugin_version,
            author=None,
            description=None,
            repository='http://localhost:9998',
            url=None):

        self.plugin_type = plugin_type
        self.plugin_name = plugin_name
        self.plugin_version = plugin_version
        self.author = author
        self.description = description
        self.repository = repository
        self.url = url

        self._repo_client = SlprClient(self.repository)

    




class SlprClient():
    def __init__(self, url):
        self.url = url

        self.db_md5 = None
        self.db_sha256 = None
        self.db = None 

    def get_database(self):

        r = self.requests.get(self.url + '/db')
        return r.json()

    def compare_plugin_version(self, t, n, v):
        db



    def download_plugin(self, t, n, v, dest):

        plugin_zip = '%s.%s-%s.zip' % (t,n,v)

        plugin_url = self.url + '/repo/%s/%s/%s/%s' % (t,n,v,plugin_zip)

        r = self.requests

