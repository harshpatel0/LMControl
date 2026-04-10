import builtins

DEBUG = True  # or load from env/config

_real_print = builtins.print

def print(*args, **kwargs):
    if DEBUG:
        _real_print(*args, **kwargs)

builtins.print = print