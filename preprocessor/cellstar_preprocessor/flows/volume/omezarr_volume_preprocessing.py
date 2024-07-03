# TODO: figure out how to use these internal volume attributes
# volume_force_dtype=preprocessor_input.volume.force_volume_dtype,
# downsampling_parameters=preprocessor_input.downsampling,

import gc

import zarr
from cellstar_db.models import AxisName
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.zarr_methods import create_dataset_wrapper
from cellstar_preprocessor.model.volume import InternalVolume

# TODO: support 3 axes case?


def omezarr_volume_preprocessing(v: InternalVolume):
    root = v.get_zarr_root()
    v.set_volume_custom_data()
    w = v.get_omezarr_wrapper()
    # PROCESSING VOLUME
    volume_data_gr: zarr.Group = root.create_group(VOLUME_DATA_GROUPNAME)

    multiscale = w.get_image_multiscale()
    axes = multiscale.axes

    omezarr_root = w.get_image_group()
    for volume_arr_resolution, volume_arr in omezarr_root.arrays():
        size_of_data_for_lvl = 0
        volume_channels_annotations = v.set_volume_channel_annotations()
        resolution_group = volume_data_gr.create_group(volume_arr_resolution)
        if len(axes) == 5 and axes[0].name == AxisName.t:
            for i in range(volume_arr.shape[0]):
                time_group = resolution_group.create_group(str(i))
                for j in range(volume_arr.shape[1]):
                    corrected_volume_arr_data = volume_arr[...][i][j].swapaxes(0, 2)
                    target_annotations = list(
                        filter(
                            lambda a: a.channel_id == str(j),
                            volume_channels_annotations,
                        )
                    )
                    assert (
                        len(target_annotations) <= 1
                    ), "More than one channel with the same ID"
                    label = j
                    if len(target_annotations) == 1:
                        target_annotation = target_annotations[0]
                        if "label" in target_annotation:
                            label = target_annotation["label"]

                    channel_arr = create_dataset_wrapper(
                        zarr_group=time_group,
                        name=label,
                        shape=corrected_volume_arr_data.shape,
                        data=corrected_volume_arr_data,
                        dtype=corrected_volume_arr_data.dtype,
                        params_for_storing=v.params_for_storing,
                    )

                    size_of_data_for_lvl = size_of_data_for_lvl + root.store.getsize(
                        channel_arr.path
                    )
                    del corrected_volume_arr_data
                    gc.collect()

        elif len(axes) == 4 and axes[0].name == AxisName.c:
            time_group = resolution_group.create_group("0")
            for j in range(volume_arr.shape[0]):
                corrected_volume_arr_data = volume_arr[...][j].swapaxes(0, 2)
                channel_arr = create_dataset_wrapper(
                    zarr_group=time_group,
                    name=j,
                    shape=corrected_volume_arr_data.shape,
                    data=corrected_volume_arr_data,
                    dtype=corrected_volume_arr_data.dtype,
                    params_for_storing=v.params_for_storing,
                )
                size_of_data_for_lvl = size_of_data_for_lvl + root.store.getsize(
                    channel_arr.path
                )
                del corrected_volume_arr_data
                gc.collect()
        else:
            raise Exception("Axes number/order is not supported")

        size_of_data_for_lvl_mb = size_of_data_for_lvl / 1024**2
        print(f"size of data for lvl in mb: {size_of_data_for_lvl_mb}")
        if (
            v.downsampling_parameters.max_size_per_downsampling_lvl_mb
            and size_of_data_for_lvl_mb
            > v.downsampling_parameters.max_size_per_downsampling_lvl_mb
        ):
            print(f"Data for resolution {volume_arr_resolution} removed for volume")
            del volume_data_gr[volume_arr_resolution]

    print("Volume processed")

    original_resolution = w.get_image_resolutions()[0]
    if v.downsampling_parameters.remove_original_resolution:
        if original_resolution in volume_data_gr:
            del volume_data_gr[original_resolution]
            print("Original resolution data removed for volume")

    if v.downsampling_parameters.max_downsampling_level is not None:
        for downsampling, downsampling_gr in volume_data_gr.groups():
            if int(downsampling) > v.downsampling_parameters.max_downsampling_level:
                del volume_data_gr[downsampling]
                print(f"Data for downsampling {downsampling} removed for volume")

    if v.downsampling_parameters.min_downsampling_level is not None:
        for downsampling, downsampling_gr in volume_data_gr.groups():
            if (
                int(downsampling) < v.downsampling_parameters.min_downsampling_level
                and downsampling != original_resolution
            ):
                del volume_data_gr[downsampling]
                print(f"Data for downsampling {downsampling} removed for volume")

    if len(sorted(volume_data_gr.group_keys())) == 0:
        raise Exception(
            f"No downsamplings will be saved: max_size_per_downsampling_lvl_mb {v.downsampling_parameters.max_size_per_downsampling_lvl_mb} is too low"
        )
