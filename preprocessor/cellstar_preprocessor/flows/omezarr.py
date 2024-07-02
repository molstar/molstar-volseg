from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal
from cellstar_db.models import OMEZarrAttrs, OMEZarrAxesType, SpatialAxisUnit, OMEZarrTimeAxesUnits, TimeTransformation
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from pydantic import BaseModel, Extra
import zarr

@dataclass
class OMEZarrWrapper:
    path: Path
    
    def get_image_resolutions(self):
        r_str = self.get_root().array_keys()
        return sorted([int(r) for r in r_str])
    
    def get_root(self):
        return open_zarr(self.path)
    
    def get_root_zattrs_wrapper(self):
        return OMEZarrAttrs.parse_obj(self.get_root().attrs)
    
    def get_multiscale(self):
        '''Only the first multiscale'''
        # NOTE: can be multiple multiscales, here picking just 1st
        return self.get_root_zattrs_wrapper().multiscales[0]
    
    def get_axes(self):
        '''Root level axes, not present in majority of used OMEZarrs'''
        raise NotImplementedError()
    
    def get_omero_channels(self):
        return self.get_root_zattrs_wrapper().omero.channels
    
    def get_time_units(self):
        m = self.get_multiscale()
        axes = m.axes
        t_axis = axes[0]
        assert t_axis.type is not None
        if t_axis.type == OMEZarrAxesType.time:
            if t_axis.unit is not None:
                return t_axis.unit
        # if first axes is not time
        return OMEZarrTimeAxesUnits.millisecond
    
    def set_zattrs(self, new_zattrs: dict[str, Any]):
        root = self.get_root()
        root.attrs.put(new_zattrs)
        print(f'New zattrs: {root.attrs}')
        
    def add_defaults_to_ome_zarr_attrs(self):
        zattrs = self.get_root_zattrs_wrapper()
        axes = zattrs.multiscales[0].axes
        for axis in axes:
            if axis.unit is None:
                if axis.type is not None:
                    if axis.type == OMEZarrAxesType.space:
                        axis.unit = SpatialAxisUnit.angstrom
                    elif axis.type == OMEZarrAxesType.time:
                        axis.unit = OMEZarrTimeAxesUnits.millisecond
                        
        self.set_zattrs(zattrs.dict())
        
    def process_time_transformations(self):
        # NOTE: can be multiple multiscales, here picking just 1st
        time_transformations_list: list[TimeTransformation] = []
        multiscales = self.get_multiscale()
        axes = multiscales.axes
        datasets_meta = multiscales.datasets
        first_axis = axes[0]
        if first_axis.type == OMEZarrAxesType.time:
            for idx, level in enumerate(datasets_meta):
                assert level.coordinateTransformations[0].scale is not None, 'OMEZarr should conform to v4 specification with scale'
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
        
    
                        

        
        