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

from volume_server.src.requests.volume import GridSliceBox


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
    def convert(self, slice: ProcessedVolumeSliceData, metadata: IPreprocessedMetadata, box: GridSliceBox) -> Union[bytes, str]:  # TODO: add binary cif to the project
        writer = BinaryCIFWriter("volume_server")

        writer.start_data_block("SERVER") 
        # NOTE: the SERVER category left empty for now
        # TODO: create new category with request and responce info (e.g. query region, timing info, etc.)
        # writer.write_category(volume_info_category, [volume_info])

        volume_info = VolumeInfo(name="volume", metadata=metadata, box=box)
        volume_info_category = CategoryWriterProvider_VolumeData3dInfo()

        # volume
        if "volume_slice" in slice:
            writer.start_data_block("volume")  # Currently needs to be EM for 
            writer.write_category(volume_info_category, [volume_info])

            data_category = CategoryWriterProvider_VolumeData3d()
            writer.write_category(data_category, [np.ravel(slice["volume_slice"])])

        # segmentation
        if "segmentation_slice" in slice and slice["segmentation_slice"]["category_set_ids"] is not None:
            writer.start_data_block("segmentation_data")
            writer.write_category(volume_info_category, [volume_info])

            segmentation = slice["segmentation_slice"]

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

        binary = True
        writer.encode()
        output_stream = ConverterOutputStream()
        writer.flush(output_stream)
        return output_stream.result_binary if binary else output_stream.result_text

    def convert_metadata(self, metadata: IPreprocessedMetadata) -> object:  # TODO: add binary cif to the project
        return metadata.json_metadata()

    def convert_meshes(self, preprocessed_volume: ProcessedVolumeSliceData, metadata: IPreprocessedMetadata, downsampling: int,
                grid_size: list[int]) -> Union[bytes, str]:
        pass
