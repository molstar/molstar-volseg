from db.interface.i_preprocessed_volume import IPreprocessedVolume
from .i_volume_to_cif_converter import IVolumeToCifConverter


class FakeVolumeToCifConverter(IVolumeToCifConverter):
    def __init__(self):
        pass

    def convert(self, preprocessed_volume: IPreprocessedVolume) -> object:  # TODO: add binary cif to the project
        return preprocessed_volume
