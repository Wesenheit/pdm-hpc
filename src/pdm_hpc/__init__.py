from pdm import signals
from pdm.core import Core
from importlib.metadata import version, PackageNotFoundError

from .pre_lock import pin_found_or_error


def plugin(core: Core) -> None:
    signals.pre_lock.connect(pin_found_or_error)
