from db.interface.i_preprocessed_medatada import IPreprocessedMetadata


class FakePreprocessedMetadata(IPreprocessedMetadata):
    def lattice_ids(self) -> list[int]:
        return [0]

    def down_samplings(self, lattice_id: int) -> list[int]:
        return [0]
