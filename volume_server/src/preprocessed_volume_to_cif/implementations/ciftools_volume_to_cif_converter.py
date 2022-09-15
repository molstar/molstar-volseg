from typing import Union

import numpy as np
from ciftools.binary import BinaryCIFWriter
from ciftools.writer.base import OutputStream

from db.interface.i_preprocessed_db import ProcessedVolumeSliceData, SegmentationSliceData
from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from volume_server.src.preprocessed_volume_to_cif.i_volume_to_cif_converter import IVolumeToCifConverter
from volume_server.src.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories.segmentation_data_3d.CategoryWriter import \
    CategoryWriterProvider_SegmentationData3d
from volume_server.src.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories.segmentation_table.CategoryWriter import \
    CategoryWriterProvider_SegmentationDataTable
from volume_server.src.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories.volume_data_3d.CategoryWriter import \
    CategoryWriterProvider_VolumeData3d
from volume_server.src.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories.volume_data_3d_info.CategoryWriter import \
    CategoryWriterProvider_VolumeData3dInfo
from volume_server.src.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories.volume_data_3d_info.volume_info import \
    VolumeInfo


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
    def _add_slice_volume_info(self, writer: BinaryCIFWriter, volume: np.ndarray, metadata: IPreprocessedMetadata, downsampling: int, grid_size: list[int]):       
        volume_info_category = CategoryWriterProvider_VolumeData3dInfo()


        min_downsampling = metadata.min(downsampling)
        max_downsampling = metadata.max(downsampling)
        min_source = metadata.min(1)
        max_source = metadata.max(1)

        volume_info = VolumeInfo("em", metadata, downsampling, min_downsampling, max_downsampling, min_source, max_source, grid_size)

        # TODO: this should have it's own data and required here as Mol* uses it to determine CIF variant
        # wont be needed in the final version
        # TODO: remove and update frontend
        writer.start_data_block("SERVER") 
        writer.write_category(volume_info_category, [volume_info])

        writer.start_data_block("EM")
        writer.write_category(volume_info_category, [volume_info])

        data_category = CategoryWriterProvider_VolumeData3d()

        to_export = np.ravel(volume)
        writer.write_category(data_category, [to_export])

    def _add_slice_segmentation(self, writer: BinaryCIFWriter, segmentation: SegmentationSliceData):
        writer.start_data_block("segmentation_data")

        # table
        set_dict = segmentation["category_set_dict"]

        set_ids, segment_ids = [], []
        for k in set_dict.keys():
            for v in set_dict[k]:
                set_ids.append(k)
                segment_ids.append(v)

        table_writer_provider = CategoryWriterProvider_SegmentationDataTable()
        writer.write_category(table_writer_provider, [{
            "set_id": set_ids,
            "segment_id": segment_ids,
            "size": len(set_ids)
        }])

        # 3d_ids
        # uint32
        ids_writer_provider = CategoryWriterProvider_SegmentationData3d()
        writer.write_category(ids_writer_provider, [segmentation["category_set_ids"]])

    def _finalize(self, writer: BinaryCIFWriter, binary: bool = True):
        writer.encode()
        output_stream = ConverterOutputStream()
        writer.flush(output_stream)
        return output_stream.result_binary if binary else output_stream.result_text

    def convert(self, slice: ProcessedVolumeSliceData, metadata: IPreprocessedMetadata, downsampling: int, grid_size: list[int]) -> Union[bytes, str]:  # TODO: add binary cif to the project
        volume: np.ndarray = slice["volume_slice"]
        
        writer = BinaryCIFWriter("volume_server")

        # volume
        self._add_slice_volume_info(writer, volume, metadata, downsampling, grid_size)

        # segmentation
        # TODO: hack... need to improve more?
        if "segmentation_slice" in slice and slice["segmentation_slice"]["category_set_ids"] is not None:
            segmentation: SegmentationSliceData = slice["segmentation_slice"]
            self._add_slice_segmentation(writer, segmentation)

        return self._finalize(writer)

    def convert_metadata(self, metadata: IPreprocessedMetadata) -> object:  # TODO: add binary cif to the project
        return metadata.json_metadata()

    def convert_meshes(self, preprocessed_volume: ProcessedVolumeSliceData, metadata: IPreprocessedMetadata, downsampling: int,
                grid_size: list[int]) -> Union[bytes, str]:
        pass
