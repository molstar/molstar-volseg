from cellstar_db.models import TimeInfo
from cellstar_preprocessor.flows.constants import DEFAULT_TIME_UNITS, TIME_INFO_STANDARD
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def geometric_segmentation_metadata_preprocessing(
    s: InternalSegmentation,
):

    m = s.get_metadata()
    # segmentation is in zattrs
    gs_metadata = m.geometric_segmentation

    time_info_mapping: dict[str, TimeInfo] = {}

    gs_data = s.get_geometric_segmentation_data()
    # it is a list of objects each of which has timeframes as keys
    for gs in gs_data:
        segmentation_id = gs.segmentation_id
        gs_metadata.ids.append(segmentation_id)

        raw = s.get_raw_geometric_segmentation_input_data()[segmentation_id]

        time_units = DEFAULT_TIME_UNITS if not raw.time_units else raw.time_units
        time_info = TIME_INFO_STANDARD
        time_info.units = time_units

        primitives = gs.primitives
        first_iteration = True
        # iterate over timeframe index and ShapePrimitiveData
        for timeframe_index, shape_primitive_data in primitives.items():
            time = int(timeframe_index)
            if first_iteration:
                time_info.start = time
                first_iteration = False
            time_info.end = time

        time_info[segmentation_id] = time_info

    gs_metadata.time_info_mapping = time_info_mapping

    m.geometric_segmentation = gs_metadata

    s.set_metadata(m)
    return m
