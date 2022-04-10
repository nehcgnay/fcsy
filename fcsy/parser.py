from io import BytesIO
from abc import abstractmethod, ABC
import re
from typing import Type
from contextlib import contextmanager
from ._typing import ReadFcsBuffer as ReadFcsBufferType
from ._typing import WriteFcsBuffer as WriteFcsBufferType
from typing import Union

try:
    import boto3
except ImportError:
    boto3 = None


class ReadFcsBuffer(ABC):
    @abstractmethod
    def seek(self, position: int):
        pass

    @abstractmethod
    def read(self, number: int):
        pass

    @abstractmethod
    def close(self):
        pass


class WriteFcsBuffer(ABC):
    @abstractmethod
    def seek(self, position: int):
        pass

    @abstractmethod
    def write(self, __b: str):
        pass

    @abstractmethod
    def tell(self):
        pass

    @abstractmethod
    def close(self):
        pass


class S3Parser(ReadFcsBuffer):
    def __init__(self, path, bucket):
        if boto3 is None:
            raise ImportError(
                "This module requires boto3. Please use 'pip install fcsy[boto3] or install boto3 manually"
            )
        super().__init__()
        self.path = path
        self.bucket = bucket
        self.position = 0
        self.s3 = boto3.client("s3")

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

    def close(self):
        pass


class S3WriteBuffer(WriteFcsBuffer):
    def __init__(self, path, bucket):
        if boto3 is None:
            raise ImportError(
                "This module requires boto3. Please use 'pip install fcsy[boto3] or install boto3 manually"
            )
        super().__init__()
        self.path = path
        self.bucket = bucket
        self.s3 = boto3.client("s3")
        self.buffer = BytesIO()

    def seek(self, position: int):
        self.buffer.seek(position)

    def tell(self):
        return self.buffer.tell()

    def write(self, bytes):
        self.buffer.write(bytes)

    def close(self):
        self.seek(0)
        self.s3.upload_fileobj(self.buffer, self.bucket, self.path)


def read_path(path):
    if path.startswith("s3://"):
        match = re.match(r"s3://(.*?)/(.*?)$", path)
        return {
            "mode": "s3",
            "contents": {"bucket": match.group(1), "key": match.group(2)},
        }
    else:
        return {"mode": "local", "contents": {"path": path}}


def create_open_func(
    parser_class: Union[Type[ReadFcsBufferType], Type[WriteFcsBufferType]],
    *args,
    **kwargs,
):
    @contextmanager
    def func(path, *func_args, **func_kwargs):
        obj = parser_class(path, *args, **kwargs)
        try:
            yield obj
        finally:
            obj.close()
            pass

    return func
