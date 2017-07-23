class PluginKey(tuple):

    def __new__(cls, key):
        plugin_version = '-'.join(key.split('-')[1:])
        plugin_type, plugin_name = key.split('-')[0].split('.')
        return tuple.__new__(cls, (plugin_type, plugin_name, plugin_version))

    @property
    def plugin_type(self):
        return self[0]

    @property
    def plugin_name(self):
        return self[1]

    @property
    def plugin_version(self):
        return self[2]

    def __str__(self):
        return "%s.%s-%s" % (self.plugin_type, self.plugin_name, self.plugin_version)

    def __setattr__(self, *ignored):
        raise NotImplementedError

    def __delattr__(self, *ignored):
        raise NotImplementedError

