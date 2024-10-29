import gc

from cellstar_preprocessor.model.ometiff import read_ometiff_pyometiff
import dask.array as da
import numcodecs
import numpy as np
import zarr
from cellstar_db.models import PrimaryDescriptor
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def ometiff_segmentation_processing(s: InternalSegmentation):
    # NOTE: supports only 3D images
    pass
    # zarr_structure: zarr.Group = open_zarr(s.path)

    # s.primary_descriptor = SegmentationPrimaryDescriptor.three_d_volume

    # # create value_to_segment_id_dict artificially for each lattice
    # s.value_to_segment_id_dict = {}

    # img_array, metadata, xml_metadata = read_ometiff_pyometiff(s)

    # s.set_segmentation_custom_data()
    # set_ometiff_source_metadata(s, metadata)

    # print(f"Processing segmentation file {s.input_path}")

    # segmentation_data_gr: zarr.Group = zarr_structure.create_group(
    #     LATTICE_SEGMENTATION_DATA_GROUPNAME
    # )

    # prepared_data, artificial_channel_ids = prepare_ometiff_for_writing(
    #     img_array, metadata, s
    # )

    # if s.custom_data.segmentation_ids_mapping is None:
    #     s.custom_data.segmentation_ids_mapping = artificial_channel_ids

    # segmentation_ids_mapping: dict[str, str] = s.custom_data.segmentation_ids_mapping

    # # similar to volume do loop
    # for data_item in prepared_data:
    #     arr: da.Array = data_item.data
    #     channel_number = data_item.channel_number
    #     lattice_id = segmentation_ids_mapping[str(channel_number)]
    #     time = data_item.timeframe_index

    #     s.value_to_segment_id_dict[lattice_id] = {}
    #     arr.compute_chunk_sizes()
    #     unique = da.unique(arr)
    #     unique.compute_chunk_sizes()
    #     for value in unique:
    #         s.value_to_segment_id_dict[lattice_id][int(value)] = int(value)

    #     # TODO: create datasets etc.
    #     lattice_id_gr = segmentation_data_gr.create_group(lattice_id)

    #     # NOTE: single resolution
    #     resolution_gr = lattice_id_gr.create_group("1")

    #     # NOTE: single timeframe
    #     # time_group = resolution_gr.create_group('0')
    #     time_group: zarr.Groups = resolution_gr.create_group(time)
    #     our_arr = time_group.create_dataset(
    #         name="grid",
    #         shape=arr.shape,
    #         data=arr.compute(),
    #     )

    #     our_set_table = time_group.create_dataset(
    #         name="set_table",
    #         dtype=object,
    #         object_codec=numcodecs.JSON(),
    #         shape=1,
    #     )

    #     d = {}
    #     for value in np.unique(our_arr[...]):
    #         d[str(value)] = [int(value)]

    #     our_set_table[...] = [d]

    #     del arr
    #     gc.collect()

    # print("Segmentation processed")
