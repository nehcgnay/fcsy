from functools import update_wrapper, partial


class Bufferize:
    def __init__(self, func, mode="rb") -> None:
        update_wrapper(self, func)
        self.func = func
        self.mode = mode

    def __get__(self, obj, objtype):
        return partial(self.__call__, obj)

    def __call__(self, obj, filepath_or_buffer, *args, **kwargs):
        if type(filepath_or_buffer) is str:
            with open(filepath_or_buffer, self.mode) as fp:
                return self.func(obj, fp, *args, **kwargs)
        else:
            return self.func(obj, filepath_or_buffer, *args, **kwargs)


def bufferize(func=None, mode="rb"):
    if func:
        return Bufferize(func)
    else:

        def wrapper(func):
            return Bufferize(func, mode=mode)

        return wrapper
