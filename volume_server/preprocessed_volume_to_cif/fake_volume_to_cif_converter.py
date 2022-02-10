from .i_volume_to_cif_converter import IVolumeToCifConverter
from ..preprocessed_db.i_preprocessed_volume import IPreprocessedVolume


class FakeVolumeToCifConverter(IVolumeToCifConverter):
    def __init__(self):
        pass

    def convert(self, preprocessed_volume: IPreprocessedVolume) -> object:  # TODO: add binary cif to the project
        return preprocessed_volume.volume()
