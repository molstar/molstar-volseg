
import base64
from pydantic.dataclasses import dataclass
import logging
from pathlib import Path
import zlib
# from cellstar_preprocessor.flows.segmentation.helper_methods import extract_raw_annotations_from_sff
from cellstar_db.models import LatticeSFF, MeshElementBaseSFF, PreparedMeshData, PreparedMeshSegmentationData, PreparedSegmentation, PreparedLatticeSegmentationData, PreparedSegmentationMetadata, SFFSegmentationModel, PrimaryDescriptor, SegmentationKind
from cellstar_preprocessor.flows.common import chunk_numpy_arr, decide_np_dtype
from cellstar_preprocessor.tools.decode_base64_data.decode_base64_data import decode_base64_data
import numpy as np
from sfftkrw.schema.adapter_v0_8_0_dev1 import SFFSegmentation
import dask.array as da
from vedo import Mesh

@dataclass
class SFFWrapper:
    path: Path
    
    def create_segmentation_ids_mapping(self):
        return { str(i): str(i) for i in self.segmentation_ids }
    
    @property
    def segmentation_ids(self):
        p = self.primary_descriptor
        match p:
            case PrimaryDescriptor.mesh_list:
                return [self.path.stem]
            case PrimaryDescriptor.three_d_volume:
                return [str(i.id) for i in self.data_model.lattice_list]
    
    @property
    def sfftk_reader(self):
        return SFFSegmentation.from_file(str(self.path.resolve()))
    
    
    @property
    def data_model(self):
        obj = self.sfftk_reader.as_json()
        # fix it, should convert str to ints etc.
        return SFFSegmentationModel.model_validate(obj)
    
    
    # Data model for mapping 
    def map_value_to_segment_id(self):
        m = self.data_model
        # TODO: str?
        d: dict[str, dict[int, int]] = {}
        for segment in m.segment_list:
            lat_id = str(segment.three_d_volume.lattice_id)
            value = int(segment.three_d_volume.value)
            segment_id = int(segment.id)
            if lat_id not in d:
                d[lat_id] = {}
            d[lat_id][value] = segment_id
        return d
    
    def _lattice_data_to_np_arr(
        self,
        l: LatticeSFF
        # data: str, mode: str, endianness: str, arr_shape: tuple[int, int, int]
        
    ) -> da.Array:
        """
        Converts lattice data to dask array.
        Under the hood, decodes lattice data into zlib-zipped data, decompress it to bytes,
        and converts to np arr based on dtype (sff mode), endianness and shape (sff size)
        """
        try:
            # TODO: decompress dask?
            decoded_data = base64.b64decode(l.data)
            byteseq = zlib.decompress(decoded_data)
            np_dtype = decide_np_dtype(mode=l.mode, endianness=l.endianness)
            arr_shape = l.size.to_tuple()
            arr = np.frombuffer(byteseq, dtype=np_dtype).reshape(arr_shape, order="F")
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e
        return da.from_array(arr)
    
    def _process_lattice_segmentation_data(self):
        resolutions: list[int]= []
        l: list[PreparedLatticeSegmentationData] = []
        resolutions = [1]
        timeframe_indices = [0]
        self.value_to_segment_id_dict = self.map_value_to_segment_id()
        for lattice in self.data_model.lattice_list:
            decoded: np.ndarray = self._lattice_data_to_np_arr(
                lattice
            )
            d = PreparedLatticeSegmentationData(
                timeframe_index=0,
                resolution=1,
                nbytes=decoded.nbytes,
                segmentation_id=str(lattice.id),
                data=decoded
                
            )
            l.append(d)
        
        return PreparedSegmentation(
            data=l,
            metadata=PreparedSegmentationMetadata(
                timeframe_indices=timeframe_indices,
                resolutions=resolutions,
                segmentation_ids=self.segmentation_ids,
                value_to_segment_id_dict=self.value_to_segment_id_dict
            ),
            kind=SegmentationKind.lattice
        )
    
    def _decode_mesh_component_data(self, component: MeshElementBaseSFF):
        unchunked_component_data = decode_base64_data(
            data=component.data,
            mode=component.mode,
            endianness=component.endianness,
        )
        
        chunked_component_data = da.from_array(chunk_numpy_arr(unchunked_component_data.compute(), 3))
        return chunked_component_data
    
    def _process_mesh_segmentation_data(self):
        resolution = 1.0
        timeframe_index = 0
        segmentation_id = self.path.stem
        l: list[PreparedMeshData] = []
        for segment in self.data_model.segment_list:
            segment_id = int(segment.id)
            if segment.mesh_list is not None:
                for mesh in segment.mesh_list:
                    mesh_id = int(mesh.id)
                    vertices = self._decode_mesh_component_data(mesh.vertices)
                    triangles = self._decode_mesh_component_data(mesh.triangles)
                    normals = self._decode_mesh_component_data(mesh.normals) \
                        if mesh.normals is not None else None
                        
                    vedo_mesh = Mesh([vertices, triangles])
                    l.append(
                        PreparedMeshData(
                            vertices=vertices,
                            triangles= triangles,
                            normals = normals,
                            area = vedo_mesh.area(),
                            segment_id = segment_id,
                            mesh_id = mesh_id,
                            fraction=1.0
                        )
                    )
        
        
        
        
        return PreparedSegmentation(
            data=[
                PreparedMeshSegmentationData(
                    segmentation_id=segmentation_id,
                    timeframe_index=timeframe_index,
                    resolution=resolution,
                    nbytes=None,
                    global_mesh_list=l
                    )],
            metadata=PreparedSegmentationMetadata(
                timeframe_indices=[timeframe_index],
                resolutions=[resolution],
                segmentation_ids=[segmentation_id]
            ),
            kind=SegmentationKind.lattice
        )
    
    def process_data(self):
        primary_descriptor = self.data_model.primary_descriptor
        # would not work for non sff 
        match primary_descriptor:
            case PrimaryDescriptor.three_d_volume:
                return self._process_lattice_segmentation_data()
            case PrimaryDescriptor.mesh_list:
                return self._process_mesh_segmentation_data()
            case PrimaryDescriptor.shape_primitive_list:
                raise NotImplementedError()
            case _:
                raise ValueError()
            
        
        
    
        # for gr_name, gr in zarr_structure.lattice_list.groups():
        # # gr is a 'lattice' obj in lattice list
        #     lattice_id = str(gr.id[...])
        #     segm_arr = lattice_data_to_np_arr(
        #         data=gr.data[0],
        #         mode=gr.mode[0],
        #         endianness=gr.endianness[0],
        #         arr_shape=(gr.size.cols[...], gr.size.rows[...], gr.size.sections[...]),
        #     )

        #     lattice_gr = segm_data_gr.create_group(gr_name)
        #     value_to_segment_id_dict = internal_segmentation.value_to_segment_id_dict
        #     params_for_storing = internal_segmentation.params_for_storing

    
    def get_raw_annotations(self):
        # data_model = self.data_model
        # for lattice in data_model.lattice_list:
            
        segm_obj = self.sfftk_reader
        segm_dict = segm_obj.as_json()
        # TODO: optimize for using data model
        for lattice in segm_dict["lattice_list"]:
            del lattice["data"]
        for segment in segm_dict["segment_list"]:
            # mesh list with list of ids
            segment["mesh_list"] = [x["id"] for x in segment["mesh_list"]]

        return segm_dict
    
    @property
    def primary_descriptor(self):
        return self.sfftk_reader.primary_descriptor
    
    # def process(self):
    #     pass
        # depending on descriptor
    
    # zarr_structure: zarr.Group = open_zarr(internal_segmentation.path)

    # internal_segmentation.raw_sff_annotations = extract_raw_annotations_from_sff(
    #     segm_file_path=internal_segmentation.input_path
    # )

    # PLAN:
    # 1. Convert hff to intermediate zarr structure
    # 2. Process it with one of 2 methods (3d volume segmentation, mesh segmentation)
    # if zarr_structure.primary_descriptor[0] == b"three_d_volume":
    #     segm_data_gr: zarr.Group = zarr_structure.create_group(
    #         LATTICE_SEGMENTATION_DATA_GROUPNAME
    #     )
    #     internal_segmentation.primary_descriptor = (
    #         SegmentationPrimaryDescriptor.three_d_volume
    #     )
    #     internal_segmentation.value_to_segment_id_dict = map_value_to_segment_id(
    #         zarr_structure
    #     )
    #     _process_three_d_volume_segmentation_data(
    #         segm_data_gr, zarr_structure, internal_segmentation=internal_segmentation
    #     )
    # elif zarr_structure.primary_descriptor[0] == b"mesh_list":
    #     segm_data_gr: zarr.Group = zarr_structure.create_group(
    #         MESH_SEGMENTATION_DATA_GROUPNAME
    #     )
    #     internal_segmentation.primary_descriptor = (
    #         SegmentationPrimaryDescriptor.mesh_list
    #     )
    #     internal_segmentation.simplification_curve = make_simplification_curve(
    #         MESH_SIMPLIFICATION_N_LEVELS, MESH_SIMPLIFICATION_LEVELS_PER_ORDER
    #     )

    #     # NOTE: single mesh set group and timeframe group
    #     mesh_set_gr = segm_data_gr.create_group("0")
    #     timeframe_gr = mesh_set_gr.create_group(0)

    #     _process_mesh_segmentation_data(
    #         timeframe_gr, zarr_structure, internal_segmentation=internal_segmentation
    #     )

    # print("Segmentation processed")

