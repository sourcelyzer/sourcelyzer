SEVERITY_TRIVIAL=0
SEVERITY_MINOR=1
SEVERITY_MAJOR=2
SEVERITY_CRITICAL=3
SEVERITY_BLOCKER=4

class SettingType():
    def __init__(self, key, default=None):
        self._key = key
        self._value = default

    def get_key(self):
        return self._key

    def get_value(self):
        return self._value


class BooleanSetting(SettingType):
    def __init__(self, key, default=False):
        self._key = key
        self._value = default


class TextSetting(SettingType):
    def __init__(self, key, default=''):
        self._key = key
        self._value = default

class NumericSetting(SettingType):
    def __inti__(self, key, default=None):
        self._key = key
        self._value = default


class BaseParser():

    def __init__(self, fn):
        self.fn = fn
        

    def parse(self):
        raise NotImplementedError()

    
class BaseMessage():

    def __init__(self, **kwargs):

        prop_defaults = {
            'severity': SEVERITY_MAJOR,
            'title': None,
            'message': None,
            'fn': None,
            'lineno': None,
            'issue_id': None
        }

        for (key,default) in prop_defaults.iteritems():
            setattr(self, key, kwargs.get(key,default))
    

