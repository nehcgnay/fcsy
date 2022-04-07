from typing import Protocol


class ReadFcsBuffer(Protocol):
    def seek(self, position: int):
        pass

    def read(self, number: int):
        pass
