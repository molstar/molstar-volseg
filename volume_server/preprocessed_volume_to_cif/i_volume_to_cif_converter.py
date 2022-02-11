import abc

from db.interface.i_preprocessed_volume import IPreprocessedVolume


class IVolumeToCifConverter(abc.ABC):
    @abc.abstractmethod
    def convert(self, preprocessed_volume: IPreprocessedVolume) -> object:  # TODO: add binary cif to the project
        pass

