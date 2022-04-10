from io import BufferedRandom
from typing import Any

try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol


class ReadFcsBuffer(Protocol):
    def seek(self, position: int):
        pass

    def read(self, number: int):
        pass

    def close(self) -> Any:
        pass


class WriteFcsBuffer(Protocol):
    def seek(self, position: int):
        pass

    def tell(self) -> int:
        pass

    def write(self, __b: str) -> Any:
        pass

    def close(self) -> Any:
        pass


UpdateFcsBuffer = BufferedRandom
