from io import BufferedRandom
from typing import Protocol, Any


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
