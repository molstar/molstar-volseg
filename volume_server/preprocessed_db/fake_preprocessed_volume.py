from volume_server.preprocessed_db.i_preprocessed_volume import IPreprocessedVolume


class FakePreprocessedVolume(IPreprocessedVolume):
    def __init__(self, fake_content: str):
        self.fake_volume = fake_content

    def volume(self) -> object:
        return self.fake_volume
