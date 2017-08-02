from sourcelyzer.cli import outnl
from sourcelyzer.properties import load_from_file
import requests

class Runner():

    def __init__(self, baseUrl, prefix=None):
        self.baseUrl = baseUrl
        self.prefix = prefix
        self.rootUrl = baseUrl + prefix

        self.sessionId = None
        self.token = None

        self.cookieJar = requests.cookies.RequestsCookieJar()

    def request(self, method, url, payload=None, **kwargs):

        r = getattr(requests, method)(url, payload, cookies={
            'sourcelyzer': self.sessionId
        }, headers = {
            'Authorization': self.token
        }, **kwargs)

        r.raise_for_status()
        return r


    def login(self, username, pw):

        login_url = self.rootUrl + '/commands/authenticate'

        r = requests.post(login_url, {'username': username, 'password': pw}, cookies=self.cookieJar)
        r.raise_for_status()

        token = r.json()['token']
        self.sessionId = r.cookies['sourcelyzer']
        self.token = token



    def findProjectByKey(self, projectKey):
        search_url = self.rootUrl + '/projects'
        r = self.request('get', search_url, {'key': projectKey})
        return r.json()

    def createProject(self, projectName, projectKey):

        data = {
            'name': projectName,
            'key': projectKey
        }

        post_url = self.rootUrl + '/projects'
        r = self.request('post', post_url, json=data) 
        return r.json()

def runner(arguments):

    conffile = arguments['--config'] if arguments['--config'] != None and arguments['--config'] != False else 'sourcelyzer.properties'

    props = load_from_file(conffile)

    app = Runner(arguments['--url'], '/httpapi/v1')

    username = arguments['--user']
    password = arguments['--password']

    app.login(username, password)

    try:   
        project = app.findProjectByKey(props['sourcelyzer.project.key'])
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            project = app.createProject(props['sourcelyzer.project.name'], props['sourcelyzer.project.key'])
        else:
            raise e
    
    print(project)




