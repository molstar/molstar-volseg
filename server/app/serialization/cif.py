from typing import Union

import numpy as np
from ciftools.serialization import create_binary_writer
from db.models import MeshesData, VolumeMetadata, VolumeSliceData

from app.core.models import GridSliceBox
from app.core.timing import Timing
from app.serialization.data.meshes_for_cif import MeshesForCif
from app.serialization.data.segment_set_table import SegmentSetTable
from app.serialization.data.volume_info import VolumeInfo
from app.serialization.volume_cif_categories.meshes import (
    CategoryWriterProvider_Mesh,
    CategoryWriterProvider_MeshTriangle,
    CategoryWriterProvider_MeshVertex,
)
from app.serialization.volume_cif_categories.segmentation_data_3d import SegmentationData3dCategory
from app.serialization.volume_cif_categories.segmentation_table import SegmentationDataTableCategory
from app.serialization.volume_cif_categories.volume_data_3d import VolumeData3dCategory
from app.serialization.volume_cif_categories.volume_data_3d_info import VolumeData3dInfoCategory


def serialize_volume_slice(slice: VolumeSliceData, metadata: VolumeMetadata, box: GridSliceBox) -> Union[bytes, str]:
    writer = create_binary_writer(encoder="cellstar-volume-server")

    writer.start_data_block("SERVER")
    # NOTE: the SERVER category left empty for now
    # TODO: create new category with request and responce info (e.g. query region, timing info, etc.)
    # writer.write_category(volume_info_category, [volume_info])

    volume_info = VolumeInfo(name="volume", metadata=metadata, box=box)

    # volume
    if "volume_slice" in slice:
        writer.start_data_block("volume")  # Currently needs to be EM for
        writer.write_category(VolumeData3dInfoCategory, [volume_info])

        data_category = VolumeData3dCategory()
        writer.write_category(data_category, [np.ravel(slice["volume_slice"])])

    # segmentation
    if "segmentation_slice" in slice and slice["segmentation_slice"]["category_set_ids"] is not None:
        writer.start_data_block("segmentation_data")
        writer.write_category(VolumeData3dInfoCategory, [volume_info])

        segmentation = slice["segmentation_slice"]

        # table
        set_dict = segmentation["category_set_dict"]
        segment_set_table = SegmentSetTable.from_dict(set_dict)
        writer.write_category(SegmentationDataTableCategory, [segment_set_table])

        # 3d_ids
        # uint32
        writer.write_category(SegmentationData3dCategory, [np.ravel(segmentation["category_set_ids"])])

    return writer.encode()


def serialize_volume_info(metadata: VolumeMetadata, box: GridSliceBox) -> bytes:
    writer = create_binary_writer(encoder="cellstar-volume-server")

    writer.start_data_block("volume_info")
    volume_info = VolumeInfo(name="volume", metadata=metadata, box=box)
    writer.write_category(VolumeData3dInfoCategory, [volume_info])

    return writer.encode()


def serialize_meshes(meshes: MeshesData, metadata: VolumeMetadata, box: GridSliceBox) -> bytes:
    with Timing("  prepare meshes for cif"):
        meshes_for_cif = MeshesForCif(meshes)

    with Timing("  write categories"):
        writer = create_binary_writer(encoder="cellstar-volume-server")

        writer.start_data_block("volume_info")
        volume_info = VolumeInfo(name="volume", metadata=metadata, box=box)
        writer.write_category(VolumeData3dInfoCategory, [volume_info])

        writer.start_data_block("meshes")
        writer.write_category(CategoryWriterProvider_Mesh, [meshes_for_cif])
        writer.write_category(CategoryWriterProvider_MeshVertex, [meshes_for_cif])
        writer.write_category(CategoryWriterProvider_MeshTriangle, [meshes_for_cif])

    with Timing("  get bytes"):
        bcif = writer.encode()
    return bcif
