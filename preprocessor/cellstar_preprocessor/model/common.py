from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cellstar_db.file_system.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME, MESH_SEGMENTATION_DATA_GROUPNAME
from cellstar_db.models import AnnotationsMetadata, DownsamplingParams, InputKind, Metadata, QuantizationDtype, SegmentationKind, VolumeExtraData
from cellstar_db.models import (
    EntryData,
)
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.zarr_methods import open_zarr

@dataclass
class InternalData:
    path: Path
    input_path: Path | list[Path]
    params_for_storing: dict
    downsampling_parameters: DownsamplingParams
    entry_data: EntryData
    input_kind: InputKind

    def get_zarr_root(self):
        return open_zarr(self.path)
    
    def get_metadata(self):
        d: dict = self.get_zarr_root().attrs["metadata_dict"]
        return Metadata.parse_obj(d)
    
    def set_metadata(self, m: Metadata):
        self.get_zarr_root().attrs["metadata_dict"] = m.dict()    
    
    def get_annotations(self):
        d: dict = self.get_zarr_root().attrs["annotations_dict"]
        return AnnotationsMetadata.parse_obj(d)
    
    def set_annotations(self, a: AnnotationsMetadata):
        self.get_zarr_root().attrs["annotations_dict"] = a.dict()
        
    def get_volume_data_group(self):
        return self.get_zarr_root()[VOLUME_DATA_GROUPNAME]
    
    def get_segmentation_data_group(self, kind: SegmentationKind):
        if kind == SegmentationKind.lattice:
            return self.get_zarr_root()[LATTICE_SEGMENTATION_DATA_GROUPNAME]
        elif kind == SegmentationKind.mesh:
            return self.get_zarr_root()[MESH_SEGMENTATION_DATA_GROUPNAME]
        else:
            raise Exception('Segmentation kind is not recognized')
    
    def get_origin(self):
        ...