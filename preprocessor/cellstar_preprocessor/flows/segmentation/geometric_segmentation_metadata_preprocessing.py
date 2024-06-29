from cellstar_db.models import (
    GeometricSegmentationData,
    GeometricSegmentationInputData,
    GeometricSegmentationSetsMetadata,
    Metadata,
    TimeInfo,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.flows.constants import (
    GEOMETRIC_SEGMENTATIONS_ZATTRS,
    RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS,
)
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def geometric_segmentation_metadata_preprocessing(
    internal_segmentation: InternalSegmentation,
):
    root = open_zarr(
        internal_segmentation.path
    )
    metadata_dict: Metadata = root.attrs["metadata_dict"]

    # segmentation is in zattrs
    geometric_segmentation_sets_metadata: GeometricSegmentationSetsMetadata = (
        metadata_dict["geometric_segmentation"]
    )

    time_info_for_all_sets: dict[str, TimeInfo] = {}

    geometric_segmentation_data: list[GeometricSegmentationData] = root.attrs[
        GEOMETRIC_SEGMENTATIONS_ZATTRS
    ]
    # it is a list of objects each of which has timeframes as keys
    for gs_set in geometric_segmentation_data:
        set_id = gs_set["segmentation_id"]
        geometric_segmentation_sets_metadata["segmentation_ids"].append(set_id)

        raw_input_data = root.attrs[RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS][set_id]
        input_data = GeometricSegmentationInputData(**raw_input_data)

        time_units = (
            "millisecond" if not input_data.time_units else input_data.time_units
        )
        time_info: TimeInfo = {
            "end": 0,
            "kind": "range",
            "start": 0,
            # TODO: specify units of time in input?
            "units": time_units,
        }

        primitives = gs_set["primitives"]
        first_iteration = True
        # iterate over timeframe index and ShapePrimitiveData
        for timeframe_index, shape_primitive_data in primitives.items():
            time = int(timeframe_index)
            if first_iteration:
                time_info["start"] = time
                first_iteration = False
            time_info["end"] = time

        time_info_for_all_sets[set_id] = time_info

    geometric_segmentation_sets_metadata["time_info"] = time_info_for_all_sets

    metadata_dict["geometric_segmentation"] = geometric_segmentation_sets_metadata

    root.attrs["metadata_dict"] = metadata_dict
    return metadata_dict
