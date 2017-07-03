###
# sourcelyzer
#
# properties file parser
###

def load_from_str(conf):
    args = {}
    for line in conf.split('\n'):
        line = line.strip()
        if len(line) == 0:
            continue

        if line.startswith('#') or line.startswith(';'):
            continue

        line_parts = line.split('=')
        key = line_parts[0]
        value = '='.join(line_parts[1:])

        args[key] = value.strip()
    p = Properties(args)
    return p

def load_from_file(fn):
    try:
        with open(fn) as f:
            return load_from_str(f.read())
    except Exception as e:
        raise e



class Properties():

    def __init__(self, args):
        self._args = args
        self._hash = None

    def __getitem__(self, key):
        return self._args[key]

    def __setitem__(self, key, value):
        raise RuntimeError("Properties objects are read only")

    def __contains__(self, key):
        return key in self._args

    def __hash__(self):
        if self._hash == None:
            self._hash = hash(frozenset(self._args.items()))
        return self._hash
    
    def __repr__(self):
        props = ""

        for key in self._args:
            props += '%s=%s\n' % (key, self._args[key])

        return props

