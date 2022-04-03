import numpy as np
from ciftools.Binary.Writer.BinaryCIFWriter import BinaryCIFWriter
from ciftools.Writer.OutputStream import OutputStream

from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from volume_server.preprocessed_volume_to_cif.i_volume_to_cif_converter import IVolumeToCifConverter
from volume_server.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories.Metadata.CategoryWriter import \
    CategoryWriterProvider_Metadata


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
        pass

    def convert(self, preprocessed_volume: np.ndarray) -> object:  # TODO: add binary cif to the project
        return preprocessed_volume

    def convert_metadata(self, metadata: IPreprocessedMetadata) -> object:  # TODO: add binary cif to the project
        writer = BinaryCIFWriter("volume_server")

        # write lattice ids
        category_writer_provider = CategoryWriterProvider_Metadata()
        writer.start_data_block("metadata")
        writer.write_category(category_writer_provider, [metadata])
        writer.encode()
        output_stream = ConverterOutputStream()
        writer.flush(output_stream)
        return output_stream.result_binary
