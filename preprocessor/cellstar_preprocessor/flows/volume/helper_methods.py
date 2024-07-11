import logging
from decimal import ROUND_CEILING, Decimal, getcontext

import dask.array as da
import numpy as np
import zarr
from cellstar_db.models import AxisName, DownsamplingLevelInfo
from cellstar_preprocessor.flows.zarr_methods import create_dataset_wrapper


def get_axis_order_mrcfile(mrc_header: object):
    d = {0: AxisName.x, 1: AxisName.y, 2: AxisName.z}
    h = mrc_header
    current_order = int(h.mapc) - 1, int(h.mapr) - 1, int(h.maps) - 1
    return [d[x] for x in current_order]


def get_voxel_sizes_from_map_header(
    map_header: object, volume_downsamplings: list[DownsamplingLevelInfo]
):
    d = _ccp4_words_to_dict_mrcfile(map_header)
    ao = {d["MAPC"] - 1: 0, d["MAPR"] - 1: 1, d["MAPS"] - 1: 2}

    N = d["NC"], d["NR"], d["NS"]
    N = N[ao[0]], N[ao[1]], N[ao[2]]

    START = d["NCSTART"], d["NRSTART"], d["NSSTART"]
    START = START[ao[0]], START[ao[1]], START[ao[2]]

    original_voxel_size: tuple[float, float, float] = (
        d["xLength"] / N[0],
        d["yLength"] / N[1],
        d["zLength"] / N[2],
    )

    voxel_sizes: dict[int, tuple[float, float, float]] = {}
    for lvl in volume_downsamplings:
        rate = lvl.level
        voxel_sizes[rate] = tuple(
            [float(Decimal(i) * Decimal(rate)) for i in original_voxel_size]
        )

    return voxel_sizes


def get_origin_from_map_header(map_header: object):
    d = _ccp4_words_to_dict_mrcfile(map_header)
    ao = {d["MAPC"] - 1: 0, d["MAPR"] - 1: 1, d["MAPS"] - 1: 2}

    N = d["NC"], d["NR"], d["NS"]
    N = N[ao[0]], N[ao[1]], N[ao[2]]

    START = d["NCSTART"], d["NRSTART"], d["NSSTART"]
    START = START[ao[0]], START[ao[1]], START[ao[2]]

    original_voxel_size: tuple[float, float, float] = (
        d["xLength"] / N[0],
        d["yLength"] / N[1],
        d["zLength"] / N[2],
    )

    # voxel_sizes_in_downsamplings: dict = {}
    # for lvl in volume_downsamplings:
    #     rate = lvl.level
    #     voxel_sizes_in_downsamplings[rate] = tuple(
    #         [float(Decimal(i) * Decimal(rate)) for i in original_voxel_size]
    #     )

    # get origin of grid based on NC/NR/NSSTART variables (5, 6, 7) and original voxel size
    # Converting to strings, then to floats to make it JSON serializable (decimals are not) -> ??
    origin: tuple[float, float, float] = (
        float(str(START[0] * original_voxel_size[0])),
        float(str(START[1] * original_voxel_size[1])),
        float(str(START[2] * original_voxel_size[2])),
    )

    return origin


def generate_kernel_3d_arr(pattern: list[int]) -> np.ndarray:
    """
    Generates conv kernel based on pattern provided (e.g. [1,4,6,4,1]).
    https://stackoverflow.com/questions/71739757/generate-3d-numpy-array-based-on-provided-pattern/71742892#71742892
    """
    try:
        assert len(pattern) == 5, "pattern should have length 5"
        pattern = pattern[0:3]
        x = np.array(pattern[-1]).reshape([1, 1, 1])
        for p in reversed(pattern[:-1]):
            x = np.pad(x, mode="constant", constant_values=p, pad_width=1)

        k = (1 / x.sum()) * x
        assert k.shape == (5, 5, 5)
    except AssertionError as e:
        logging.error(e, stack_info=True, exc_info=True)
        raise e
    return k


def normalize_axis_order_mrcfile(dask_arr: da.Array, mrc_header: object) -> da.Array:
    """
    Normalizes axis order to X, Y, Z (1, 2, 3)
    """
    h = mrc_header
    current_order = int(h.mapc) - 1, int(h.mapr) - 1, int(h.maps) - 1

    if current_order != (0, 1, 2):
        print(f"Reordering axes from {current_order}...")
        ao = {v: i for i, v in enumerate(current_order)}
        # TODO: optimize this to a single transpose
        dask_arr = dask_arr.transpose().transpose(ao[2], ao[1], ao[0]).transpose()
    else:
        dask_arr = dask_arr.transpose()

    return dask_arr


def store_volume_data_in_zarr(
    data: da.Array,
    volume_data_group: zarr.Group,
    params_for_storing: dict,
    force_dtype: np.dtype,
    resolution: str,
    timeframe_index: str,
    channel_id: str,
):
    assert channel_id is not None
    resolution_data_group: zarr.Group = volume_data_group.require_group(resolution)
    time_frame_data_group = resolution_data_group.require_group(timeframe_index)

    zarr_arr = create_dataset_wrapper(
        zarr_group=time_frame_data_group,
        data=data,
        name=str(channel_id),
        shape=data.shape,
        dtype=force_dtype,
        params_for_storing=params_for_storing,
        is_empty=True,
    )

    # da.to_zarr(arr=data, url=zarr_arr, overwrite=True, compute=True)


# could be method of internal volume?
def _ccp4_words_to_dict_mrcfile(mrc_header: object) -> dict:
    """input - mrcfile object header (mrc.header)"""
    ctx = getcontext()
    ctx.rounding = ROUND_CEILING
    d = {}

    m = mrc_header
    # mrcfile implementation
    d["NC"], d["NR"], d["NS"] = int(m.nx), int(m.ny), int(m.nz)
    d["NCSTART"], d["NRSTART"], d["NSSTART"] = (
        int(m.nxstart),
        int(m.nystart),
        int(m.nzstart),
    )
    d["xLength"] = round(Decimal(float(m.cella.x)), 5)
    d["yLength"] = round(Decimal(float(m.cella.y)), 5)
    d["zLength"] = round(Decimal(float(m.cella.z)), 5)
    d["MAPC"], d["MAPR"], d["MAPS"] = int(m.mapc), int(m.mapr), int(m.maps)

    return d
