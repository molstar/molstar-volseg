from os import path

from .fake_preprocessed_volume import FakePreprocessedVolume
from .i_preprocessed_db import IPreprocessedDb
from .i_preprocessed_volume import IPreprocessedVolume


class FakePreprocessedDb(IPreprocessedDb):
    @staticmethod
    def __path_to_object__(namespace: str, key: str) -> str:
        return path.join("../..", namespace, key)

    async def contains(self, namespace: str, key: str) -> bool:
        return True  # path.isfile(self.__path_to_object__(namespace, key))

    async def store(self, namespace: str, key: str, value: object) -> bool:
        return True

    async def read(self, namespace: str, key: str) -> IPreprocessedVolume:
        """
        if not self.contains(namespace, key):
            return None  # TODO: throw instead?

        zarr_file_path = self.__path_to_object__(namespace, key)
        store = zarr.ZipStore(zarr_file_path, mode='r')

        #
        root = zarr.group(store)
        # Print out some data
        print(root.details[...])

        lattice_list = root.lattice_list.groups()
        for gr_name, gr in lattice_list:
            data = decompress_lattice_data(
                gr.data[0],
                gr.mode[0],
                (gr.size.cols[...], gr.size.rows[...], gr.size.sections[...]))
            # Original lattice data as np arr (not downsampled)
            print('Lattice data in original resolution:')
            print(data)

            for arr_name, arr in gr.downsampled_data.arrays():
                print(f'Downsampled data by the factor of {arr_name}')
                print(arr[...])
                """
        return FakePreprocessedVolume("Fake volume for key: " + key)
