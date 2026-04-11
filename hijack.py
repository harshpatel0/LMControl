import builtins

DEBUG = True

_real_print = builtins.print

def print(*args, **kwargs):
    if DEBUG:
        _real_print(*args, **kwargs)

builtins.print = print