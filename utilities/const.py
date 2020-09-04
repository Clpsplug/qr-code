"""
Constant type in Python.
"""
import sys


class _const:
    class ConstError(TypeError):
        pass

    def __setattr__(self, key, value):
        if key in self.__dict__:
            raise self.ConstError("Can't re-bind const (%s) (You are trying to overwrite constants!" % key)
        self.__dict__[key] = value


sys.modules[__name__] = _const()
