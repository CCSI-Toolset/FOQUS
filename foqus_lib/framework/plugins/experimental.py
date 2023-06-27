try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points

from types import ModuleType


def get_plugins(group_name: str = "foqus.plugins") -> dict[str, ModuleType]:
    ...
