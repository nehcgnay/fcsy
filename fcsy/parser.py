from io import IOBase
from typing import Type
from contextlib import contextmanager

try:
    import boto3
except ImportError:
    boto3 = None


class S3Parser(IOBase):
    def __init__(self, path, bucket, region_name):
        if boto3 is None:
            raise ImportError(
                "This module requires boto3. Please use 'pip install fcsy[boto3] or install boto3 manually"
            )
        super().__init__()
        self.path = path
        self.bucket = bucket
        self.position = 0
        self.s3 = boto3.client("s3", region_name)

    def seek(self, position: int):
        self.position = position

    def read(self, number: int):
        resp = self.s3.get_object(
            Bucket=self.bucket,
            Key=self.path,
            Range=f"bytes={self.position}-{self.position+number}",
        )
        self.position += number
        return resp["Body"].read(number)


def create_open_func(parser_class: Type[IOBase], *args, **kwargs):
    @contextmanager
    def func(path, *func_args, **func_kwargs):
        try:
            yield parser_class(path, *args, **kwargs)
        finally:
            pass

    return func
