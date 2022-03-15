

class Plugin:
    plugin_modules_available = {}
    plugin_modules_unavailable = {}
    module = None

    @classmethod
    def available(cls):
        return tuple(cls.plugin_modules_available.values())

    @classmethod
    def unavailable(cls):
        return tuple(cls.plugin_modules_unavailable.values())

    @classmethod
    def load(cls):
        instance = cls.plugin_modules_available.get(cls.python_module_name)
        if instance is not None:
            return instance
        instance = cls()
        try:
            exec('import %s' %(instance.python_module_name))
        except ModuleNotFoundError:
            cls.plugin_modules_unavailable[instance.python_module_name] = instance
            raise
        self._module = eval(instance.python_module_name)
        cls.plugin_modules_available[instance.python_module_name] = instance
        return instance

    @classmethod
    def load_capture_error(cls):
        instance = None
        try:
            instance = cls.load()
        except ModuleNotFoundError:
            pass
        return instance

    def __init__(self):
        self._module = None

    @property
    def module(self):
        return self._module


class PsuadePlugin(Plugin):
    """
    plugin = PsuadePlugin.load()
    if plugin == None:  print("unavailable")
    elif plugin.nomad is False: print("nomand unavailable")
    """
    python_module_name='psuade'

    @property
    def nomad(self):
        return False

class TensorFlowPlugin(Plugin):
    python_module_name='tensorflow'
