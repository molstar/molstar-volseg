
import base64
from dataclasses import dataclass
import logging
from pathlib import Path
import zlib
# from cellstar_preprocessor.flows.segmentation.helper_methods import extract_raw_annotations_from_sff
from cellstar_db.models import LatticeSFF, MeshElementBaseSFF, PreparedMeshData, PreparedMeshSegmentationData, PreparedSegmentation, PreparedLatticeSegmentationData, PreparedSegmentationMetadata, SFFSegmentationModel, SegmentationPrimaryDescriptor
from cellstar_preprocessor.flows.common import chunk_numpy_arr, decide_np_dtype
from cellstar_preprocessor.tools.decode_base64_data.decode_base64_data import decode_base64_data
import numpy as np
from sfftkrw.schema.adapter_v0_8_0_dev1 import SFFSegmentation
import dask.array as da
from vedo import Mesh

@dataclass
class SFFWrapper:
    path: Path
    
    
    # 1. do post init
    # 2. in it set reader to sff segmentation
    # 3. set raw annotations dict
    # create pydantic model from it
    
    def create_segmentation_ids_mapping(self):
        return { str(i): str(i) for i in self.segmentation_ids }
    
    @property
    def segmentation_nums(self):
        # lattice nums
        return [int(l.id) for l in self.data_model.lattice_list]
    
    @property
    def segmentation_ids(self):
        # lattice nums
        return [str(i) for i in self.segmentation_nums]
    
    @property
    def sfftk_reader(self):
        return SFFSegmentation.from_file(str(self.path.resolve()))
    
    
    @property
    def data_model(self):
        obj = self.sfftk_reader.as_json()
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
        # can pass object
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
            np_dtype = decide_np_dtype(mode=l.mode, endianness=l.endianness.value)
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
                
            )
            d = PreparedLatticeSegmentationData(
                timeframe_index=0,
                resolution=1,
                size=decoded.nbytes,
                segmentation_id=str(lattice.id),
                data=decoded
                
            )
            l.append(d)
        
        return PreparedSegmentation(
            data=l,
            metadata=PreparedSegmentationMetadata(
                timeframe_indices=timeframe_indices,
                resolutions=resolutions,
                segmentation_nums=self.segmentation_nums,
                segmentation_ids=self.segmentation_ids
            )    
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
        resolution = 1
        timeframe_index = 0
        segmentation_id = "0"
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
                        
                    # TODO: use compute here if does not work
                    # TODO: pre downsample more here if does not work
                    # too big
                    vedo_mesh = Mesh([vertices, triangles])
                    l.append(
                        PreparedMeshData(
                            vertices=vertices,
                            triangles= triangles,
                            normals = normals,
                            area = vedo_mesh.area(),
                            segment_id = segment_id,
                            mesh_id = mesh_id
                        )
                    )
        
        
        
        
    #     unchunked_component_data = decode_base64_data(
    #     data=mesh[mesh_component_name].data[...][0],
    #     mode=mesh[mesh_component_name].mode[...][0],
    #     endianness=mesh[mesh_component_name].endianness[...][0],
    # )
    # # chunked onto triples
    # chunked_component_data = chunk_numpy_arr(unchunked_component_data, 3)

    # component_arr = create_dataset_wrapper(
    #     zarr_group=target_group,
    #     data=chunked_component_data,
    #     name=mesh_component_name,
    #     shape=chunked_component_data.shape,
    #     dtype=chunked_component_data.dtype,
    #     params_for_storing=params_for_storing,
    # )

    # component_arr.attrs[f"num_{mesh_component_name}"] = int(
    #     mesh[mesh_component_name][f"num_{mesh_component_name}"][...]
    # )
        
        return PreparedSegmentation(
            data=[
                PreparedMeshSegmentationData(
                    segmentation_id=segmentation_id,
                    timeframe_indices=timeframe_index,
                    resolution=resolution,
                    size=None,
                    mesh_list=l
                    )],
            metadata=PreparedSegmentationMetadata(
                timeframe_indices=[timeframe_index],
                resolutions=[resolution],
                segmentation_nums=self.segmentation_nums,
                segmentation_ids=self.segmentation_ids
            )    
        )
                        
                        
        # for segment_name, segment in zarr_structure.segment_list.groups():
        #     segment_id = int(segment.id[...])
        #     single_segment_group = timeframe_gr.create_group(segment_id)
        #     single_detail_lvl_group = single_segment_group.create_group(1)
            # if "mesh_list" in segment:
            #     for mesh_name, mesh in segment.mesh_list.groups():
            #         mesh_id = int(mesh.id[...])
            #         single_mesh_group = single_detail_lvl_group.create_group(mesh_id)

            #         for mesh_component_name, mesh_component in mesh.groups():
            #             if mesh_component_name != "id":
            #                 write_mesh_component_data_to_zarr_arr(
            #                     target_group=single_mesh_group,
            #                     mesh=mesh,
            #                     mesh_component_name=mesh_component_name,
            #                     params_for_storing=params_for_storing,
            #                 )
            #         # TODO: check in which units is area and volume
            #         vertices = single_mesh_group["vertices"][...]
            #         triangles = single_mesh_group["triangles"][...]
            #         vedo_mesh_obj = Mesh([vertices, triangles])
            #         single_mesh_group.attrs["num_vertices"] = (
            #             single_mesh_group.vertices.attrs["num_vertices"]
            #         )
            #         single_mesh_group.attrs["area"] = vedo_mesh_obj.area()
            #         # single_mesh_group.attrs['volume'] = vedo_mesh_obj.volume()

    
    def process_data(self):
        primary_descriptor = self.data_model.primary_descriptor
        match primary_descriptor:
            case SegmentationPrimaryDescriptor.three_d_volume:
                return self._process_lattice_segmentation_data()
            case SegmentationPrimaryDescriptor.mesh_list:
                return self._process_mesh_segmentation_data()
            case SegmentationPrimaryDescriptor.shape_primitive_list:
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

