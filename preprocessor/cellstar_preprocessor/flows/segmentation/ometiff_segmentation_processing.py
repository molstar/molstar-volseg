import gc

import dask.array as da
import numcodecs
import numpy as np
import zarr
from cellstar_preprocessor.flows.common import (
    open_zarr_structure_from_path,
    prepare_ometiff_for_writing,
    read_ometiff_to_dask,
    set_ometiff_source_metadata,
    set_segmentation_custom_data,
)
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_db.models import SegmentationPrimaryDescriptor
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def ometiff_segmentation_processing(internal_segmentation: InternalSegmentation):
    # NOTE: supports only 3D images

    zarr_structure: zarr.Group = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )

    internal_segmentation.primary_descriptor = (
        SegmentationPrimaryDescriptor.three_d_volume
    )

    # create value_to_segment_id_dict artificially for each lattice
    internal_segmentation.value_to_segment_id_dict = {}

    img_array, metadata, xml_metadata = read_ometiff_to_dask(internal_segmentation)

    set_segmentation_custom_data(internal_segmentation, zarr_structure)
    set_ometiff_source_metadata(internal_segmentation, metadata)

    print(f"Processing segmentation file {internal_segmentation.input_path}")

    segmentation_data_gr: zarr.Group = zarr_structure.create_group(
        LATTICE_SEGMENTATION_DATA_GROUPNAME
    )

    prepared_data, artificial_channel_ids = prepare_ometiff_for_writing(
        img_array, metadata, internal_segmentation
    )

    if "channel_ids_mapping" not in internal_segmentation.custom_data:
        internal_segmentation.custom_data["channel_ids_mapping"] = (
            artificial_channel_ids
        )

    channel_ids_mapping: dict[str, str] = internal_segmentation.custom_data[
        "segmentation_ids_mapping"
    ]

    # similar to volume do loop
    for data_item in prepared_data:
        arr: da.Array = data_item["data"]
        channel_number = data_item["channel_number"]
        lattice_id = channel_ids_mapping[str(channel_number)]
        time = data_item["time"]

        internal_segmentation.value_to_segment_id_dict[lattice_id] = {}
        arr.compute_chunk_sizes()
        unique = da.unique(arr)
        unique.compute_chunk_sizes()
        for value in unique:
            internal_segmentation.value_to_segment_id_dict[lattice_id][int(value)] = (
                int(value)
            )

        # TODO: create datasets etc.
        lattice_id_gr = segmentation_data_gr.create_group(lattice_id)

        # NOTE: single resolution
        resolution_gr = lattice_id_gr.create_group("1")

        # NOTE: single timeframe
        # time_group = resolution_gr.create_group('0')
        time_group: zarr.Groups = resolution_gr.create_group(time)
        our_arr = time_group.create_dataset(
            name="grid",
            shape=arr.shape,
            data=arr.compute(),
        )

        our_set_table = time_group.create_dataset(
            name="set_table",
            dtype=object,
            object_codec=numcodecs.JSON(),
            shape=1,
        )

        d = {}
        for value in np.unique(our_arr[...]):
            d[str(value)] = [int(value)]

        our_set_table[...] = [d]

        del arr
        gc.collect()

    print("Segmentation processed")
