import abc
from typing import List


class IPreprocessedMetadata(abc.ABC):
    @abc.abstractmethod
    def lattice_ids(self) -> List[int]:  # TODO: assign type to volume
        pass

    @abc.abstractmethod
    def down_samplings(self, lattice_id: int) -> List[int]:  # TODO: assign type to volume
        pass
