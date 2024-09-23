import os
import importlib


package_dir = os.path.dirname(__file__)


modules = [f[:-3] for f in os.listdir(package_dir) if f.endswith('.py') and f != '__init__.py']


for module in modules:
    importlib.import_module(f'{__name__}.{module}')


__all__ = []
for module in modules:
    mod = importlib.import_module(f'{__name__}.{module}')
    for attr in dir(mod):
        if not attr.startswith('_'):
            globals()[attr] = getattr(mod, attr)
            __all__.append(attr)
