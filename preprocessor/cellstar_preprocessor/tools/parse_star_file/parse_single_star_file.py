import argparse
import json
from pathlib import Path

import starfile
from cellstar_db.models import (
    GeometricSegmentationInputData,
    ShapePrimitiveInputData,
    ShapePrimitiveKind,
    SphereInputParams,
)
from cellstar_preprocessor.model.common import hex_to_rgba_normalized


# divisor = 4
def parse_single_star_file(
    path: Path,
    sphere_radius: float,
    sphere_color: list[float],
    pixel_size: float,
    star_file_coordinate_divisor: int,
    segmentation_id: str,
):
    lst: list[ShapePrimitiveInputData] = []
    df = starfile.read(str(path.resolve()))
    for index, row in df.iterrows():
        # micrograph_name = row['rlnTomoName'].split('_')
        # row["rlnTomoName"]
        # radius = 0.08 * 200
        radius = sphere_radius
        color = sphere_color

        sp_input_data = ShapePrimitiveInputData(
            kind=ShapePrimitiveKind.sphere,
            parameters=SphereInputParams(
                id=index,
                # kind=ShapePrimitiveKind.sphere,
                center=(
                    row["rlnCoordinateX"] / star_file_coordinate_divisor * pixel_size,
                    row["rlnCoordinateY"] / star_file_coordinate_divisor * pixel_size,
                    row["rlnCoordinateZ"] / star_file_coordinate_divisor * pixel_size,
                ),
                color=color,
                radius=radius,
            ),
        )

        lst.append(sp_input_data)
    d = {0: lst}
    geometric_segmentation_input = GeometricSegmentationInputData(
        segmentation_id=segmentation_id, shape_primitives_input=d
    )

    return geometric_segmentation_input


def parse_script_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--star_file_path", type=str, help="")
    parser.add_argument("--geometric_segmentation_input_file_path", type=str, help="")
    parser.add_argument("--sphere_radius", type=float)
    parser.add_argument("--segmentation_id", type=str)
    parser.add_argument("--sphere_color_hex", type=str)
    parser.add_argument("--pixel_size", type=float)
    parser.add_argument("--star_file_coordinate_divisor", type=int, default=4)
    args = parser.parse_args()
    return args


def main(args: argparse.Namespace):
    star_file_path = Path(args.star_file_path)
    sphere_radius = args.sphere_radius
    sphere_color_hex: str = args.sphere_color_hex
    pixel_size = args.pixel_size
    star_file_coordinate_divisor = args.star_file_coordinate_divisor
    geometric_segmentation_input_file_path = Path(
        args.geometric_segmentation_input_file_path
    )

    sphere_color = hex_to_rgba_normalized(sphere_color_hex)

    lst = parse_single_star_file(
        path=star_file_path,
        sphere_radius=sphere_radius,
        sphere_color=sphere_color,
        pixel_size=pixel_size,
        star_file_coordinate_divisor=star_file_coordinate_divisor,
        segmentation_id=args.segmentation_id,
    )
    with (geometric_segmentation_input_file_path).open("w") as fp:
        json.dump(lst.dict(), fp, indent=4)


if __name__ == "__main__":
    args = parse_script_args()
    main(args)
