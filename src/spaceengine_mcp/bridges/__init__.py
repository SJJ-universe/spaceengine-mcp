from .script_bridge import ScriptBridge
from .catalog_bridge import CatalogBridge

__all__ = [
    "ScriptBridge",
    "CatalogBridge",
]

# 추가 브릿지 — 모듈 단위 import (클래스가 아닌 모듈 함수 제공)
_optional_modules = [
    "log_bridge",
    "config_bridge",
    "state_bridge",
    "keyboard_bridge",
    "flight_bridge",
]

import importlib as _importlib
for _mod_name in _optional_modules:
    try:
        _mod = _importlib.import_module(f".{_mod_name}", package=__name__)
        globals()[_mod_name] = _mod
    except (ImportError, SyntaxError):
        pass
