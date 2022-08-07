import abc

from ciftools.src.binary.encoding.types import EncodedCIFData


class CIFEncoderBase(abc.ABC):
    @abc.abstractmethod
    def encode(self, data: object) -> EncodedCIFData:
        pass
