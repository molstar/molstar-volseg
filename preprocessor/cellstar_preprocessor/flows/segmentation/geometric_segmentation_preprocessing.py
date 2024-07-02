import json
from pathlib import Path
from uuid import uuid4

import zarr
from cellstar_db.models import (
    Box,
    BoxInputParams,
    Cylinder,
    Ellipsoid,
    EllipsoidInputParams,
    GeometricSegmentationData,
    GeometricSegmentationInputData,
    Pyramid,
    PyramidInputParams,
    ShapePrimitiveBase,
    ShapePrimitiveData,
    ShapePrimitiveKind,
    Sphere,
    SphereInputParams,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.flows.constants import (
    GEOMETRIC_SEGMENTATIONS_ZATTRS,
    RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS,
)
from cellstar_preprocessor.model.segmentation import InternalSegmentation


# should return tuple - segmentation_id, primitives
def _process_geometric_segmentation_data(
    data: GeometricSegmentationInputData
):
    shape_primitives_input = data.shape_primitives_input
    segmentation_id = data.segmentation_id

    primitives: dict[int, ShapePrimitiveData] = {}

    for timeframe_index, timeframe_data in shape_primitives_input.items():
        shape_primitives_processed: list[ShapePrimitiveBase] = []

        for sp in timeframe_data:
            params = sp.parameters
            kind = sp.kind
            segment_id = params.id
            # color = params.color

            if kind == ShapePrimitiveKind.sphere:
                params: SphereInputParams
                shape_primitives_processed.append(
                    Sphere(
                        kind=kind,
                        center=params.center,
                        id=segment_id,
                        radius=params.radius,
                    )
                )
            elif kind == ShapePrimitiveKind.cylinder:
                params: SphereInputParams
                shape_primitives_processed.append(
                    Cylinder(
                        kind=kind,
                        start=params.start,
                        end=params.end,
                        radius_bottom=params.radius_bottom,
                        radius_top=params.radius_top,
                        id=segment_id,
                    )
                )
            elif kind == ShapePrimitiveKind.box:
                params: BoxInputParams
                shape_primitives_processed.append(
                    Box(
                        kind=kind,
                        translation=params.translation,
                        scaling=params.scaling,
                        rotation=params.rotation.dict(),
                        id=segment_id,
                    )
                )
            elif kind == ShapePrimitiveKind.ellipsoid:
                params: EllipsoidInputParams
                shape_primitives_processed.append(
                    Ellipsoid(
                        kind=kind,
                        dir_major=params.dir_major,
                        dir_minor=params.dir_minor,
                        center=params.center,
                        radius_scale=params.radius_scale,
                        id=segment_id,
                    )
                )
            elif kind == ShapePrimitiveKind.pyramid:
                params: PyramidInputParams
                shape_primitives_processed.append(
                    Pyramid(
                        kind=kind,
                        translation=params.translation,
                        scaling=params.scaling,
                        rotation=params.rotation.dict(),
                        id=segment_id,
                    )
                )
            else:
                raise Exception(f"Shape primitive kind {kind} is not supported")

        # at the end
        d = ShapePrimitiveData(shape_primitive_list=shape_primitives_processed)
        primitives[timeframe_index] = d

    return segmentation_id, primitives


def geometric_segmentation_preprocessing(s: InternalSegmentation):
    input_paths: list[Path] = s.input_path

    for input_path in input_paths:
        if input_path.suffix == ".json":
            with open(str(input_path.resolve()), "r", encoding="utf-8") as f:
                json_data = json.load(f)
        else:
            raise Exception("Geometric segmentation input is not supported")

        raw_input_data = GeometricSegmentationInputData.parse_obj(json_data)
        custom_segmentation_id, primitives = _process_geometric_segmentation_data(
            data=raw_input_data
        )
        segmentation_id = str(uuid4())
        if custom_segmentation_id:
            segmentation_id = custom_segmentation_id

        d=GeometricSegmentationData(
            segmentation_id=segmentation_id,
            primitive=primitives,
        )
        s.add_raw_geometric_segmentation_input_data(raw_input_data)
        s.add_geometric_segmentation_data(d)

        print("Geometric segmentation processed")
