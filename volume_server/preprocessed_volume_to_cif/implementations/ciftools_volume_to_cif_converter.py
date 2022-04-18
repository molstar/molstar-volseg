import json
from typing import Union

import numpy as np
from ciftools.binary import BinaryCIFWriter
from ciftools.writer.base import OutputStream

from db.interface.i_preprocessed_db import ProcessedVolumeSliceData, SegmentationSliceData
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
    def _add_slice_volume(self, writer: BinaryCIFWriter, one_dimensional_volume: np.ndarray):
        category_writer_provider = CategoryWriterProvider_VolumeData3d()
        writer.start_data_block("volume_data_3d")
        print("adding slice volume of size: " + str(one_dimensional_volume.size))
        writer.write_category(category_writer_provider, [one_dimensional_volume])

    def _add_slice_segmentations(self, writer: BinaryCIFWriter, segmentation: SegmentationSliceData):
        set_ids = segmentation["category_set_ids"]
        set_dict = segmentation["category_set_dict"]
        print("Segmentation ids: " + str(set_ids.size) + " -> " + str(set_ids.flatten().data))
        print("Segmentation dict: " + str(set_dict))
        pass

    def _finalize(self, writer: BinaryCIFWriter, binary: bool = True):
        writer.encode()
        output_stream = ConverterOutputStream()
        writer.flush(output_stream)
        print("Stream binary: " + str(output_stream.result_binary))
        print("Stream text: " + str(output_stream.result_text))
        return output_stream.result_binary if binary else output_stream.result_text

    def convert(self, slice: ProcessedVolumeSliceData) -> Union[bytes, str]:  # TODO: add binary cif to the project
        volume: np.ndarray = slice["volume_slice"]
        segmentation: SegmentationSliceData = slice["segmentation_slice"]

        writer = BinaryCIFWriter("volume_server")
        self._add_slice_volume(writer, np.ravel(volume))
        self._add_slice_segmentations(writer, segmentation)

        return self._finalize(writer)

    def convert_metadata(self, metadata: IPreprocessedMetadata) -> object:  # TODO: add binary cif to the project
        return json.dumps(metadata.__dict__)
