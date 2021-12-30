import functools

# separator that doesn't collide with syntax for shells and commands
ALTERNATE_SEPARATOR = "¦"


def string_to_bool(param):
    if not isinstance(param, str):
        return param
    if param.upper() in ["1", "TRUE", "T", "Y", "YES"]:
        return True
    elif param.upper() in ["0", "FALSE", "F", "N", "NO"]:
        return False
    else:
        return param


def quoted_string(param):
    if isinstance(param, bool):
        return '"1"' if param else '"0"'
    if isinstance(param, (int, float, str)):
        return f'"{str(param)}"'
    return param


def string_to_list(param):
    split_char = ALTERNATE_SEPARATOR if ALTERNATE_SEPARATOR in param else ","
    return param if not isinstance(param, str) else [_.strip() for _ in param.split(split_char)]


# https://stackoverflow.com/a/13653312/4728007
def fullname(o):
    module = o.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return o.__class__.__name__
    return module + "." + o.__class__.__name__


already_called = {}


def once(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = fullname(func)
        if not already_called.get(key):
            already_called[key] = True
            func(*args, **kwargs)
        return

    return wrapper
