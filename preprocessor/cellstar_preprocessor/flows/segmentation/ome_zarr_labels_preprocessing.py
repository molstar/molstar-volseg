# TODO: figure out how to use
# params_for_storing=self.preprocessor_input.storing_params,
# downsampling_parameters=self.preprocessor_input.downsampling,

import gc

import numcodecs
import numpy as np
import zarr
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def ome_zarr_labels_preprocessing(internal_segmentation: InternalSegmentation):
    ome_zarr_root = zarr.open_group(internal_segmentation.input_path)

    our_zarr_structure = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )

    segmentation_data_gr = our_zarr_structure.create_group(
        LATTICE_SEGMENTATION_DATA_GROUPNAME
    )

    # root_zattrs = ome_zarr_root.attrs
    # multiscales = root_zattrs["multiscales"]
    # # NOTE: can be multiple multiscales, here picking just 1st
    # axes = multiscales[0]["axes"]

    # NOTE: hack to support NGFFs where image has time dimension > 1 and label has time dimension = 1
    original_resolution = ome_zarr_root.attrs["multiscales"][0]["datasets"][0]["path"]

    for label_gr_name, label_gr in ome_zarr_root.labels.groups():
        label_gr_zattrs = label_gr.attrs
        label_gr_multiscales = label_gr_zattrs["multiscales"]
        # NOTE: can be multiple multiscales, here picking just 1st
        axes = label_gr_multiscales[0]["axes"]
        lattice_id_gr: zarr.Group = segmentation_data_gr.create_group(label_gr_name)
        # arr_name is resolution
        for arr_name, arr in label_gr.arrays():
            size_of_data_for_lvl = 0
            our_resolution_gr = lattice_id_gr.create_group(arr_name)
            if len(axes) == 5 and axes[0]["name"] == "t":
                # NOTE: hack to support NGFFs where image has time dimension > 1 and label has time dimension = 1
                # there are two cases
                # 1. Label has time dimension 1, image 18
                # 2. Label has time dimension 40, image 40
                # 1. => iterate over 18, but the data should be taken
                # 2. => iterate over time dimension of label normally
                # we can do a hack
                # if time dimension of label is < that of image, we do not
                # check anything, but just copy the first frame for all frames
                # of label
                image_time_dimension = ome_zarr_root[original_resolution].shape[0]
                label_time_dimension = arr.shape[0]

                wrong_time_dimension = False
                if label_time_dimension < image_time_dimension:
                    print(
                        f"Time dimension of label {label_time_dimension} is lower than time dimension of image {image_time_dimension}"
                    )
                    print(
                        "Label data is artificially expanded to time dimension of image using the data of the first label timeframe"
                    )
                    time_dimension = image_time_dimension
                    wrong_time_dimension = True
                else:
                    time_dimension = label_time_dimension
                for i in range(time_dimension):
                    time_group: zarr.Group = our_resolution_gr.create_group(str(i))
                    channel_dimension = arr.shape[1]
                    assert (
                        channel_dimension == 1
                    ), "NGFFs with labels having more than one channel are not supported"
                    # before it was
                    # corrected_arr_data = arr[...][arr.shape[0] - 1][channel_dimension - 1].swapaxes(0, 2)
                    if wrong_time_dimension:
                        time_index = arr.shape[0] - 1
                    else:
                        time_index = i
                    corrected_arr_data = arr[...][time_index][
                        channel_dimension - 1
                    ].swapaxes(0, 2)
                    # i8 is not supported by CIFTools
                    if corrected_arr_data.dtype == "i8":
                        corrected_arr_data = corrected_arr_data.astype("i4")
                    our_arr = time_group.create_dataset(
                        name="grid",
                        shape=corrected_arr_data.shape,
                        data=corrected_arr_data,
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

                    # NOTE: here check size of both arr and set_table
                    size_of_data_for_lvl = (
                        size_of_data_for_lvl
                        + our_zarr_structure.store.getsize(our_set_table.path)
                        + our_zarr_structure.store.getsize(our_arr.path)
                    )

                    del corrected_arr_data
                    gc.collect()

            elif len(axes) == 4 and axes[0]["name"] == "c":
                time_group: zarr.Group = our_resolution_gr.create_group("0")
                channel_dimension = arr.shape[0]
                assert (
                    channel_dimension == 1
                ), "NGFFs with labels having more than one channel are not supported"
                corrected_arr_data = arr[...][channel_dimension - 1].swapaxes(0, 2)
                if corrected_arr_data.dtype == "i8":
                    corrected_arr_data = corrected_arr_data.astype("i4")
                our_arr = time_group.create_dataset(
                    name="grid",
                    shape=corrected_arr_data.shape,
                    data=corrected_arr_data,
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

                # NOTE: here check size of both arr and set_table
                size_of_data_for_lvl = (
                    size_of_data_for_lvl
                    + our_zarr_structure.store.getsize(our_set_table.path)
                    + our_zarr_structure.store.getsize(our_arr.path)
                )

                del corrected_arr_data
                gc.collect()

            # elif len(axes) == 3:
            # # NOTE: assumes CYX order
            #     if axes[0]["name"] == 'c':
            #         time_group = our_resolution_gr.create_group("0")
            #         for j in range(arr.shape[0]):
            #             # swap Y and X
            #             corrected_arr_data = arr[...][j].swapaxes(0, 1)
            #             # add Z dimension = 1
            #             corrected_arr_data = np.expand_dims(corrected_arr_data, axis=2)
            #             assert corrected_arr_data.shape[2] == 1

            #             if corrected_arr_data.dtype == "i8":
            #                 corrected_arr_data = corrected_arr_data.astype("i4")

            #             our_channel_group = time_group.create_group(str(j))
            #             our_arr = our_channel_group.create_dataset(
            #                 name="grid",
            #                 shape=corrected_arr_data.shape,
            #                 data=corrected_arr_data,
            #             )

            #             our_set_table = our_channel_group.create_dataset(
            #                 name="set_table",
            #                 dtype=object,
            #                 object_codec=numcodecs.JSON(),
            #                 shape=1,
            #             )

            #             d = {}
            #             for value in np.unique(our_arr[...]):
            #                 d[str(value)] = [int(value)]

            #             our_set_table[...] = [d]
            #     else:
            #         pass
            else:
                raise Exception("Axes number/order is not supported")

            size_of_data_for_lvl_mb = size_of_data_for_lvl / 1024**2
            print(f"size of data for lvl in mb: {size_of_data_for_lvl_mb}")
            if (
                internal_segmentation.downsampling_parameters.max_size_per_downsampling_lvl_mb
                and size_of_data_for_lvl_mb
                > internal_segmentation.downsampling_parameters.max_size_per_downsampling_lvl_mb
            ):
                print(f"Data for resolution {arr_name} removed for segmentation")
                del lattice_id_gr[arr_name]

        all_resolutions = sorted(label_gr.array_keys())
        original_resolution = all_resolutions[0]
        if internal_segmentation.downsampling_parameters.remove_original_resolution:
            del lattice_id_gr[original_resolution]
            print("Original resolution data removed for segmentation")

        if (
            internal_segmentation.downsampling_parameters.max_downsampling_level
            is not None
        ):
            for downsampling, downsampling_gr in lattice_id_gr.groups():
                if (
                    int(downsampling)
                    > internal_segmentation.downsampling_parameters.max_downsampling_level
                ):
                    del lattice_id_gr[downsampling]
                    print(
                        f"Data for downsampling {downsampling} removed for segmentation"
                    )

        if (
            internal_segmentation.downsampling_parameters.min_downsampling_level
            is not None
        ):
            for downsampling, downsampling_gr in lattice_id_gr.groups():
                if (
                    int(downsampling)
                    < internal_segmentation.downsampling_parameters.min_downsampling_level
                    and downsampling != original_resolution
                ):
                    del lattice_id_gr[downsampling]
                    print(
                        f"Data for downsampling {downsampling} removed for segmentation"
                    )

        if len(sorted(lattice_id_gr.group_keys())) == 0:
            raise Exception(
                f"No downsamplings will be saved: max_size_per_downsampling_lvl_mb {internal_segmentation.downsampling_parameters.max_size_per_downsampling_lvl_mb} is too low"
            )
    print("Labels processed")
