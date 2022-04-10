from functools import update_wrapper, partial

from .parser import create_open_func, read_path, S3Parser, S3WriteBuffer


class Bufferize:
    def __init__(self, func, mode="rb") -> None:
        update_wrapper(self, func)
        self.func = func
        self.mode = mode

    def __get__(self, obj, objtype):
        return partial(self.__call__, obj)

    def __call__(self, obj, filepath_or_buffer, *args, **kwargs):
        if type(filepath_or_buffer) is str:
            path = read_path(filepath_or_buffer)
            if path["mode"] == "s3":
                if self.mode == "rb":
                    buffer_class = S3Parser
                elif self.mode == "wb":
                    buffer_class = S3WriteBuffer
                else:
                    raise ValueError("invalid s3 buffer mode")

                open_func = create_open_func(
                    buffer_class, bucket=path["contents"]["bucket"]
                )
                with open_func(path["contents"]["key"], self.mode) as fp:
                    return self.func(obj, fp, *args, **kwargs)
            else:
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
