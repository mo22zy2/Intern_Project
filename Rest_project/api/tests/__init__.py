from unittest.mock import patch
from django.template.context import BaseContext

_real_base_copy = BaseContext.__copy__


def _safe_base_context_copy(self):
    try:
        return _real_base_copy(self)
    except AttributeError:
        duplicate = object.__new__(type(self))
        duplicate.dicts = self.dicts[:]
        return duplicate


patch.object(BaseContext, "__copy__", _safe_base_context_copy).start()
