import numpy

from db.interface.i_preprocessed_volume import IPreprocessedVolume


class FakePreprocessedVolume(IPreprocessedVolume):
    def __init__(self, fake_content: numpy.ndarray):
        self.fake_volume = fake_content

    def get_data(self) -> numpy.ndarray:
        return self.fake_volume
