import os
import imp

def load_plugins(plugins_dir):
    type_dirs = [f for f in os.listdir(plugins_dir) if os.path.isdir(os.path.join(plugins_dir, f))]

    mods = {}

    for plugin_type in type_dirs:

        mods[plugin_type] = {}

        plugin_type_dir = os.path.join(plugins_dir, plugin_type)

        plugin_dirs = [f for f in os.listdir(plugin_type_dir) if os.path.isdir(os.path.join(plugin_type_dir, f))]

        for plugin in plugin_dirs:
            plugin_dir = os.path.join(plugin_type_dir, plugin)
    
            plugin_mod = load_plugin(plugin_type_dir, plugin)

            mods[plugin_type][plugin] = plugin_mod

    return mods


def load_plugin(root_dir, plugin_name):
    fp, pathname, description = imp.find_module(plugin_name, [root_dir,])
    mod = imp.load_module(plugin_name, fp, pathname, description)
    return mod


