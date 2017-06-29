###
# config.py
#
# Project configuration parser
###

def parse_line(ln):
    ln = ln.split('=')
    key = ln[0]
    value = '='.join(ln[1:])
    return (key,value.strip())

class ProjectConfig():

    def __init__(self, **kwargs):

        self._properties = {}

        prop_defaults = {
            'sourcelyzer.project.name': '',
            'sourcelyzer.project.version': '',
            'sourcelyzer.project.key': '',
            'sourcelyzer.source.rootDir': '.',
            'sourcelyzer.source.encoding': 'utf-8'
        }

        for (prop, default) in prop_defaults.iteritems():
            self._properties[prop] = kwargs.get(prop, default)

    def getProjectName(self):
        return self._properties['sourcelyzer.project.name']

    def getProjectVersion(self):
        return self._properties['sourcelyzer.project.version']

    def getProjectKey(self):
        return self._properties['sourcelyzer.project.key']

    def getSourceDir(self):
        return self._properties['sourcelyzer.source.rootDir']

    def getSourceEncoding(self):
        return self._properties['sourcelyzer.source.encoding']


def ParseConfigFile(fn):
    with open(fn) as f:
        args = {}
        for ln in f.readlines():
            key,value = parse_line(ln)
            args[key] = value

        pc = ProjectConfig(**args)
        return pc

