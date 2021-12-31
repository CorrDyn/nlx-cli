import functools
import json
from types import SimpleNamespace

from nlx.utils.misc import basic_logger

logger = None


def get_logger():
    # avoid circular import
    global logger
    if not logger:
        from conf.settings import NLX_LOG_LEVEL

        logger = basic_logger(__name__, NLX_LOG_LEVEL)
    return logger


class DictNamespace(dict):
    """
    DictNamespace items are accessible as index or attributes,
    e.g. foo["bar"] == foo.bar
    """

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = self.construct_namespace(value)

    def __delattr__(self, key):
        del self[key]

    @classmethod
    def construct_namespace(cls, maybe_dict):
        if isinstance(maybe_dict, dict):
            for key, value in maybe_dict.items():
                if isinstance(value, dict):
                    maybe_dict[key] = cls(**value)
                elif isinstance(value, SimpleNamespace):
                    maybe_dict[key] = cls(**value.__dict__)
                else:
                    maybe_dict[key] = value
        return maybe_dict

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        DictNamespace.construct_namespace(self)


def get_all(dict_obj, *keys):
    return tuple(dict_obj.get(key, None) for key in keys)


def as_json(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        try:
            return json.dumps(result, indent=2, default=str)
        except:  # noqa
            get_logger().exception("Error while serializing object to json")
            return json.dumps(dict(error="never", result=str(result)), indent=2, default=str)

    return wrapper
