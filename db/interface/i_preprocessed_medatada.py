import abc


class IPreprocessedMetadata(abc.ABC):
    @abc.abstractmethod
    def lattice_ids(self) -> list[int]:  # TODO: assign type to volume
        pass

    @abc.abstractmethod
    def down_samplings(self, lattice_id: int) -> list[int]:  # TODO: assign type to volume
        pass
