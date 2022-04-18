import json

import numpy as np
from ciftools.binary import BinaryCIFWriter
from ciftools.writer.base import OutputStream

from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from volume_server.preprocessed_volume_to_cif.i_volume_to_cif_converter import IVolumeToCifConverter
from volume_server.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories.volume_data_3d.CategoryWriter import \
    CategoryWriterProvider_VolumeData3d


class ConverterOutputStream(OutputStream):
    result_binary: bytes = None
    result_text: str = ""

    def write_string(self, data: str) -> bool:
        self.result_text = data
        return True

    def write_binary(self, data: bytes) -> bool:
        self.result_binary = data
        return True


class CifToolsVolumeToCifConverter(IVolumeToCifConverter):
    def __init__(self):
        self._writer = BinaryCIFWriter("volume_server")

    def convert(self, preprocessed_volume: np.ndarray) -> object:  # TODO: add binary cif to the project
        print("convert preprocessed_volume with size " + str(preprocessed_volume.size))
        category_writer_provider = CategoryWriterProvider_VolumeData3d()
        self._writer.start_data_block("volume_data_3d")
        self._writer.write_category(category_writer_provider, [preprocessed_volume])
        self._writer.encode()
        output_stream = ConverterOutputStream()
        self._writer.flush(output_stream)
        return preprocessed_volume

    def convert_metadata(self, metadata: IPreprocessedMetadata) -> object:  # TODO: add binary cif to the project
        return json.dumps(metadata.__dict__)
