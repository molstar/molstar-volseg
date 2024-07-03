from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cellstar_db.models import (
    AxisName,
    OMEZarrAttrs,
    SpatialAxisUnit,
    TimeAxisUnit,
    TimeTransformation,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr

# OMEZARR_AXIS_NUMBER_TO_NAME_ORDER = {
#     0:
# }


@dataclass
class OMEZarrWrapper:
    path: Path

    def get_image_resolutions(self):
        r_str = self.get_zarr_root().array_keys()
        return sorted([int(r) for r in r_str])
    
    def get_label_resolutions(self, label_gr_name: str):
        r_str = self.get_labels()[label_gr_name].group_keys()
        return sorted([int(r) for r in r_str])

    def get_zarr_root(self):
        return open_zarr(self.path)

    def get_labels(self):
        return self.get_zarr_root().labels

    def get_labels_group_names(self):
        return self.get_labels().group_keys()

    def get_root_zattrs_wrapper(self):
        return OMEZarrAttrs.parse_obj(self.get_zarr_root().attrs)

    def get_label_group_zattrs_wrapper(self, label_group_name: str):
        return OMEZarrAttrs.parse_obj(self.get_labels()[label_group_name].attrs)

    def get_multiscale(self):
        """Only the first multiscale"""
        # NOTE: can be multiple multiscales, here picking just 1st
        return self.get_root_zattrs_wrapper().multiscales[0]

    def get_axes(self):
        """Root level axes, not present in majority of used OMEZarrs"""
        raise NotImplementedError()

    def get_omero_channels(self):
        return self.get_root_zattrs_wrapper().omero.channels

    def get_time_units(self):
        m = self.get_multiscale()
        axes = m.axes
        t_axis = axes[0]
        # change to ax
        if t_axis.name == AxisName.t:
            if t_axis.unit is not None:
                return t_axis.unit
        # if first axes is not time
        return TimeAxisUnit.millisecond

    def set_zattrs(self, new_zattrs: dict[str, Any]):
        root = self.get_zarr_root()
        root.attrs.put(new_zattrs)
        print(f"New zattrs: {root.attrs}")

    def add_defaults_to_ome_zarr_attrs(self):
        zattrs = self.get_root_zattrs_wrapper()
        axes = zattrs.multiscales[0].axes
        for axis in axes:
            if axis.unit is None:
                # if axis.type is not None:
                if axis.name in [AxisName.x, AxisName.y, AxisName.z]:
                    axis.unit = SpatialAxisUnit.angstrom
                elif axis.name == AxisName.t:
                    axis.unit = TimeAxisUnit.millisecond

        self.set_zattrs(zattrs.dict())

    def process_time_transformations(self):
        # NOTE: can be multiple multiscales, here picking just 1st
        time_transformations_list: list[TimeTransformation] = []
        multiscales = self.get_multiscale()
        axes = multiscales.axes
        datasets_meta = multiscales.datasets
        first_axis = axes[0]
        if first_axis.name == AxisName.t:
            for idx, level in enumerate(datasets_meta):
                assert (
                    level.coordinateTransformations[0].scale is not None
                ), "OMEZarr should conform to v4 specification with scale"
                scale_arr = level.coordinateTransformations[0].scale
                if len(scale_arr) == 5:
                    factor = scale_arr[0]
                    if multiscales.coordinateTransformations is not None:
                        if multiscales.coordinateTransformations[0].type == "scale":
                            factor = (
                                factor
                                * multiscales.coordinateTransformations[0].scale[0]
                            )
                    time_transformations_list.append(
                        TimeTransformation(downsampling_level=level.path, factor=factor)
                    )
                else:
                    raise Exception("Length of scale arr is not supported")

            return time_transformations_list
        else:
            return time_transformations_list
