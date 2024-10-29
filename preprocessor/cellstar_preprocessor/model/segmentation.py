from dataclasses import field
import math
from cellstar_preprocessor.flows.common import compute_downsamplings_to_be_stored, compute_number_of_downsampling_steps
# from cellstar_preprocessor.flows.segmentation.helper_methods import compute_vertex_density, simplify_mesh
from cellstar_preprocessor.model.map import MapWrapper
from cellstar_preprocessor.model.vedo import VedoMesh
from cellstar_preprocessor.tools.magic_kernel_downsampling_3d.magic_kernel_downsampling_3d import MagicKernel3dDownsampler
from cellstar_preprocessor.tools.parse_map.parse_map import parse_map
from cellstar_preprocessor.tools.tiff_stack_to_da_arr.tiff_stack_to_da_arr import tiff_stack_to_da_arr
from numpy import isin
from pydantic.dataclasses import dataclass
import gc
from typing import Any
from cellstar_preprocessor.flows.segmentation.category_set_downsampling_methods import downsample_categorical_data, store_downsampling_levels_in_zarr
import dask.array as da
import zarr
from cellstar_db.models import (
    AxisName,
    DataKind,
    DetailLvlsMetadata,
    DownsamplingLevelDict,
    ExtraData,
    AssetKind,
    MeshComponentNumbers,
    MeshElementName,
    MeshZattrs,
    MeshesMetadata,
    MeshListMetadata,
    MeshMetadata,
    PreparedLatticeSegmentationData,
    PreparedMeshData,
    PreparedMeshSegmentationData,
    PreparedSegmentation,
    PreparedSegmentationMetadata,
    SamplingInfo,
    SegmentationExtraData,
    SegmentationKind,
    PrimaryDescriptor,
    SegmentationSetTable,
    StoringParams,
)
from cellstar_preprocessor.flows.constants import (
    BLANK_SAMPLING_INFO,
    DOWNSAMPLING_KERNEL,
    LATTICE_SEGMENTATION_DATA_GROUPNAME,
    MESH_SEGMENTATION_DATA_GROUPNAME,
    MESH_VERTEX_DENSITY_THRESHOLD,
    MESH_ZATTRS_NAME,
    MIN_GRID_SIZE,
    TIME_INFO_STANDARD,
    VOLUME_DATA_GROUPNAME,
)
# from cellstar_preprocessor.flows.segmentation.helper_methods import hdf5_to_zarr
from cellstar_preprocessor.flows.zarr_methods import create_dataset_wrapper, get_downsamplings
from cellstar_preprocessor.model.internal_data import InternalData

@dataclass
class InternalSegmentation(InternalData):
    custom_data: SegmentationExtraData | None = None
    primary_descriptor: PrimaryDescriptor | None = None
    value_to_segment_id_dict: dict[str, dict[int, int]] = field(default_factory=dict)
    simplification_curve: dict[int, float] = field(default_factory=dict)
    raw_sff_annotations: dict[str, Any] = field(default_factory=object)
    map_headers: dict[str, object] = field(default_factory=dict)
    prepared: PreparedSegmentation | None = None
    
    def get_mask_wrappers(self):
        assert isinstance(self.input_path, list)
        voxel_size = self.custom_data.voxel_size if self.custom_data.voxel_size is not None\
            else None
        ws: list[MapWrapper] = []
        # need to return a collection of map wrappers
        for p in self.input_path:
            ws.append(
                MapWrapper(
                    path=p,
                    voxel_size=voxel_size,
                    kind=DataKind.segmentation
                )
            )
        return ws
            
    def _prepare_tiff_stack_segmenation(self):
        self.primary_descriptor = (
            PrimaryDescriptor.three_d_volume
        )
        w = self.get_tiff_stack_wrapper()
        data = w.to_array
        # TODO: can tiff have channels?
        
        lattice_id = self.custom_data.segmentation_ids_mapping[
            self.input_path.stem
        ]
        
        value_to_segment_id_dict = {}
        value_to_segment_id_dict[lattice_id] = {}
        for value in da.unique(data).compute():
            value_to_segment_id_dict[lattice_id][int(value)] = int(value)
            
        l: list[PreparedLatticeSegmentationData] = [
            PreparedLatticeSegmentationData(
                timeframe_index=0,
                resolution=1,
                nbytes=data.nbytes,
                # from file name
                segmentation_id=lattice_id,
                data=data
            )]
        return PreparedSegmentation(
            data=l,
            metadata=PreparedSegmentationMetadata(
                timeframe_indices=[0],
                resolutions=[0],
                segmentation_ids=[lattice_id],
                value_to_segment_id_dict=value_to_segment_id_dict
            )
        )
    
    def _prepare_mask_segmenation(self):
        self.primary_descriptor = PrimaryDescriptor.three_d_volume
        ws = self.get_mask_wrappers()        
        segmentation_ids_mapping: dict[str, str] = self.custom_data.segmentation_ids_mapping
        for w in ws:
            parsed_mask = w.parsed
            lattice_id = segmentation_ids_mapping[w.path.stem]
            self.map_headers[lattice_id] = parsed_mask.header
            self.value_to_segment_id_dict[lattice_id] = {}
            for value in da.unique(parsed_mask.data).compute():
                self.value_to_segment_id_dict[lattice_id][int(value)] = int(value)
        
    def _prepare_ometiff_segmentation(self):
        self.primary_descriptor = PrimaryDescriptor.three_d_volume
        w = self.get_ometiff_wrapper()
        return w.prepare_segmentation_data()
        
    # TODO: should change metadata as well
    def _downsample_lattice_segmentation(self):
        prepared_downsamplings: list[PreparedLatticeSegmentationData] = []
        for idx, p in enumerate(self.prepared.data):
            # print(f'Iteration #{idx}: downsampling data - {p}')
            d = p.data
            segmentation_id = p.segmentation_id
            timeframe_index = p.timeframe_index
            if 1 in d.shape:
                print(
                    f"Downsampling skipped for segmentation {segmentation_id}, timeframe {timeframe_index} since one of the dimensions is equal to 1"
                )
                continue
            
            
            # make this block of code into a function and reuse in volume downsampling
            downsampling_steps = compute_number_of_downsampling_steps(
                downsampling_parameters=self.downsampling_parameters,
                min_grid_size=MIN_GRID_SIZE,
                input_grid_size=math.prod(d.shape),
                factor=2**3,
                force_dtype=d.dtype,
            )

            ratios_to_be_stored = compute_downsamplings_to_be_stored(
                downsampling_parameters=self.downsampling_parameters,
                number_of_downsampling_steps=downsampling_steps,
                input_grid_size=math.prod(d.shape),
                factor=2**3,
                dtype=d.dtype,
            )
            
            
            
            levels: list[DownsamplingLevelDict] = self._create_category_set_downsamplings(
                magic_kernel=MagicKernel3dDownsampler(),
                original_data=d,
                downsampling_steps=downsampling_steps,
                ratios_to_be_stored=ratios_to_be_stored,
                # self.value_to_segment_id_dict is empty
                value_to_segment_id_dict_for_specific_lattice_id=self.value_to_segment_id_dict[
                    segmentation_id
                ]
            )
            for l in levels:
                prepared_downsamplings.append(
                    PreparedLatticeSegmentationData(
                        timeframe_index=timeframe_index,
                        resolution=l.ratio,
                        nbytes=d.nbytes,
                        segmentation_id=segmentation_id,
                        data=d
                    )
                )

        # change metadata
        self.prepared.metadata.resolutions = self.prepared.metadata.resolutions + ratios_to_be_stored
        
        return prepared_downsamplings


    def _downsample_mesh_segmentation(self):
        prepared_downsamplings: list[PreparedMeshSegmentationData] = []
        simplification_curve: dict[int, float] = (
            self.simplification_curve
        )
        density_threshold = MESH_VERTEX_DENSITY_THRESHOLD["area"]
        # mesh set_id => timeframe => segment_id => detail_lvl => mesh_id in meshlist

        for idx, p in enumerate(self.prepared.data):
            # print(f'Iteration #{idx}: downsampling data - {p}')
            p: PreparedMeshSegmentationData
            global_mesh_list = p.global_mesh_list
            for prepared_mesh_data in global_mesh_list:
                for level, fraction in simplification_curve.items():
                    vedo_mesh = VedoMesh(
                                        vertice=prepared_mesh_data.vertices,
                                        triangles=prepared_mesh_data.triangles
                                        )
                    if (
                        density_threshold != 0
                        and vedo_mesh.compute_vertex_density()
                        <= density_threshold
                    ):
                        break
                    if fraction == 1:
                        continue  # original data, don't need to compute anything
                    downsampled_mesh_data = vedo_mesh.simplify_mesh(
                        mesh_id=prepared_mesh_data.mesh_id,
                        segment_id=prepared_mesh_data.segment_id,
                        fraction=fraction,
                    )
                    
                    # check each mesh in mesh_data_dict if it contains 0 vertices
                            # remove all such meshes from dit
                    if downsampled_mesh_data.vertices.shape[0] == 0:
                        raise Exception(f"Mesh with segment ID {downsampled_mesh_data.segment_id} has no vertices")
                    
                    prepared_downsamplings.append(downsampled_mesh_data)
        
        self.prepared.metadata.resolutions = self.prepared.metadata.resolutions + [int(i) for i in simplification_curve.keys()]
                    
        return prepared_downsamplings

        
    def _create_category_set_downsamplings(
        self,
        magic_kernel: MagicKernel3dDownsampler,
        original_data: da.Array,
        downsampling_steps: int,
        ratios_to_be_stored: list,
        # data_group: zarr.Group,
        value_to_segment_id_dict_for_specific_lattice_id: dict,
        # params_for_storing: dict,
    ) -> list[DownsamplingLevelDict]:
        """
        Take original segmentation data, do all downsampling levels, create zarr datasets for each
        """
        # table with just singletons, e.g. "104": {104}, "94" :{94}
        initial_set_table = SegmentationSetTable(
            original_data, value_to_segment_id_dict_for_specific_lattice_id
        )

        # for now contains just x1 downsampling lvl dict, in loop new dicts for new levels are appended
        levels = [
            DownsamplingLevelDict(
                ratio=1, grid=original_data, set_table=initial_set_table
                # {"ratio": 1, "grid": original_data, "set_table": initial_set_table}
            )
        ]
        for i in range(downsampling_steps):
            current_set_table = SegmentationSetTable(
                original_data, value_to_segment_id_dict_for_specific_lattice_id
            )
            # on first iteration (i.e. when doing x2 downsampling), it takes original_data and initial_set_table with set of singletons
            levels.append(
                downsample_categorical_data(magic_kernel, levels[i], current_set_table)
            )
        
        
        # TO
        # remove original data, as they are already stored
        levels.pop(0)
        # remove all with ratios that are not in ratios_to_be_stored
        levels = [level for level in levels if level.ratio in ratios_to_be_stored]
        
        return levels
        # TODO: convert this to PreparedSegmentationData
        
        
        
    # TODO: should downsample mesh here
    def downsample(self):
        # TODO: other?
        prepared_downsamplings: list[PreparedLatticeSegmentationData | PreparedMeshSegmentationData] = []
        match self.input_kind:
            case AssetKind.omezarr:
                # further downsample omezarr if needed? there are cases
                print('Skipping downsampling of omezarr')
            case _:
                for i in self.prepared.metadata.resolutions:
                    assert i in [0, 1], 'Original prepared data must contain no downsamplings'
                
                # TODO: should work for any segmentation not just sff
                match self.primary_descriptor:
                    case PrimaryDescriptor.three_d_volume:
                        prepared_downsamplings = self._downsample_lattice_segmentation()
                    case PrimaryDescriptor.mesh_list:
                        prepared_downsamplings = self._downsample_mesh_segmentation()
                    case _:
                        raise NotImplementedError()
                
            # case _:
            #     raise NotImplementedError()
        self.prepared.data = self.prepared.data + prepared_downsamplings
        print("Segmentation downsampled")
        
        
        # match self.primary_descriptor:
        #     case SegmentationPrimaryDescriptor.three_d_volume:
        #         for lattice_gr_name,
                
        #     for lattice_gr_name, lattice_gr in zarr_structure[
        #         LATTICE_SEGMENTATION_DATA_GROUPNAME
        #     ].groups():
        #         original_res_gr: zarr.Group = lattice_gr["1"]
        #         for time, time_gr in original_res_gr.groups():
        #             original_data_arr = original_res_gr[time].grid
        #             lattice_id = lattice_gr_name

        #             segmentation_downsampling_steps = compute_number_of_downsampling_steps(
        #                 int_vol_or_seg=internal_segmentation,
        #                 min_grid_size=MIN_GRID_SIZE,
        #                 input_grid_size=math.prod(original_data_arr.shape),
        #                 force_dtype=original_data_arr.dtype,
        #                 factor=2**3,
        #             )

        #             ratios_to_be_stored = compute_downsamplings_to_be_stored(
        #                 int_vol_or_seg=internal_segmentation,
        #                 number_of_downsampling_steps=segmentation_downsampling_steps,
        #                 input_grid_size=math.prod(original_data_arr.shape),
        #                 dtype=original_data_arr.dtype,
        #                 factor=2**3,
        #             )

        #             _create_category_set_downsamplings(
        #                 magic_kernel=MagicKernel3dDownsampler(),
        #                 original_data=original_data_arr[...],
        #                 downsampling_steps=segmentation_downsampling_steps,
        #                 ratios_to_be_stored=ratios_to_be_stored,
        #                 data_group=lattice_gr,
        #                 value_to_segment_id_dict_for_specific_lattice_id=internal_segmentation.value_to_segment_id_dict[
        #                     lattice_id
        #                 ],
        #                 params_for_storing=internal_segmentation.params_for_storing,
        #                 time_frame=time,
        #             )

        #     # NOTE: removes original level resolution data
        #     if internal_segmentation.downsampling_parameters.remove_original_resolution:
        #         del lattice_gr[1]
        #         print("Original resolution data removed for segmentation")

        # elif (
        #     internal_segmentation.primary_descriptor
        #     == SegmentationPrimaryDescriptor.mesh_list
        # ):
        #     simplification_curve: dict[int, float] = (
        #         internal_segmentation.simplification_curve
        #     )
        #     calc_mode = "area"
        #     density_threshold = MESH_VERTEX_DENSITY_THRESHOLD[calc_mode]
        #     # mesh set_id => timeframe => segment_id => detail_lvl => mesh_id in meshlist

        #     segm_data_gr = zarr_structure[MESH_SEGMENTATION_DATA_GROUPNAME]
        #     for set_id, set_gr in segm_data_gr.groups():
        #         for timeframe_index, timeframe_gr in set_gr.groups():
        #             for segment_name_id, segment in timeframe_gr.groups():
        #                 original_detail_lvl_mesh_list_group = segment[1]
        #                 group_ref = original_detail_lvl_mesh_list_group

        #                 for level, fraction in simplification_curve.items():
        #                     if (
        #                         density_threshold != 0
        #                         and compute_vertex_density(group_ref, mode=calc_mode)
        #                         <= density_threshold
        #                     ):
        #                         break
        #                     if fraction == 1:
        #                         continue  # original data, don't need to compute anything
        #                     mesh_data_dict = simplify_meshes(
        #                         original_detail_lvl_mesh_list_group,
        #                         ratio=fraction,
        #                         segment_id=segment_name_id,
        #                     )
        #                     # TODO: potentially simplify meshes may output mesh with 0 vertices, normals, triangles
        #                     # it should not be stored?
        #                     # check each mesh in mesh_data_dict if it contains 0 vertices
        #                     # remove all such meshes from dict
        #                     for mesh_id in list(mesh_data_dict.keys()):
        #                         if mesh_data_dict[mesh_id]["attrs"]["num_vertices"] == 0:
        #                             del mesh_data_dict[mesh_id]

        #                     # if there is no meshes left in dict - break from while loop
        #                     if not bool(mesh_data_dict):
        #                         break

        #                     # mesh set_id => timeframe => segment_id => detail_lvl => mesh_id in meshlist
        #                     group_ref = store_mesh_data_in_zarr(
        #                         mesh_data_dict,
        #                         segment,
        #                         detail_level=level,
        #                         params_for_storing=internal_segmentation.params_for_storing,
        #                     )

        #                 # segment[1]
        #                 # NOTE: removes original level resolution data
        #                 if (
        #                     internal_segmentation.downsampling_parameters.remove_original_resolution
        #                 ):
        #                     del segment[1]
        #                     # print("Original resolution data removed for segmentation")
        #     if internal_segmentation.downsampling_parameters.remove_original_resolution:
        #         # del internal_segmentation.simplification_curve[1]
        #         internal_segmentation.simplification_curve.pop(1, None)

        # print("Segmentation downsampled")

    def _store_mesh_segmentation_data(self, segmentation_group: zarr.Group, prepared_data: PreparedMeshSegmentationData,
                                  params_for_storing: StoringParams):
        # segmentation id
        # res
        # time
        # meshlist
        # mesh
        # timeframes = [0]
        # resolutions = [0]
        segmentation_id = prepared_data.segmentation_id
        timeframe_index = prepared_data.timeframe_index
        
        time_group: zarr.Group = segmentation_group.create_group(
            f"{segmentation_id}/{0}"
        )
        
        

        for d in prepared_data.global_mesh_list:
            # vertices = d.vertices
            # triangles = d.triangles
            # normals = d.normals
            area = d.area
            detail_lvl = 1
            segment_gr = time_group.require_group(str(d.segment_id))
            detail_lvl_gr = segment_gr.require_group(str(detail_lvl))
            mesh_gr = detail_lvl_gr.require_group(str(d.mesh_id))
            mesh_gr.attrs[MESH_ZATTRS_NAME] = {}
        



            # print(getattr(Color, color_name).value)
            # TODO: optimize to loop

            for e in MeshElementName:
                name = e.name
                # value = e.value
                # element_array - no param shape
                # none for normals
                element_array: da.Array | None = getattr(d, name)
                if element_array is None:
                    if name =='normals' and element_array is None:
                        continue
                    else:
                        raise Exception(f'Mesh component name: {name}, array cannot be None')
                
                create_dataset_wrapper(
                    zarr_group=mesh_gr,
                    data=element_array,
                    name=name,
                    shape=element_array.shape,
                    dtype=element_array.dtype,
                    params_for_storing=params_for_storing,
                    is_empty=True
                )
                m = self.get_mesh_zattrs(segmentation_id=segmentation_id, timeframe_index=timeframe_index, segment_id=d.segment_id, detail_lvl=detail_lvl, mesh_id=d.mesh_id)
                num_element_name = f"num_{name}"
                setattr(m, num_element_name, element_array.size)
                self.set_mesh_zattrs(segmentation_id=segmentation_id, timeframe_index=timeframe_index, segment_id=d.segment_id, detail_lvl=detail_lvl, mesh_id=d.mesh_id, m=m)

            m.area = area
                # no triangles
            self.set_mesh_zattrs(segmentation_id=segmentation_id, timeframe_index=timeframe_index, segment_id=d.segment_id, detail_lvl=detail_lvl, mesh_id=d.mesh_id, m=m)


    def _store_lattice_segmentation_data(self, prepared_data: PreparedLatticeSegmentationData,
        segmentation_group: zarr.Group,
        value_to_segment_id_dict_for_specific_segmentation_id: dict[int, int],
        params_for_storing: StoringParams):
        # TODO: params
        # TODO: procedure from create_category_set_downsamplings
        # table with just singletons, e.g. "104": {104}, "94" :{94}
        # dask arrays instead
        initial_set_table = SegmentationSetTable(
            prepared_data.data, value_to_segment_id_dict_for_specific_segmentation_id
        )

        # just x1 downsampling lvl dict
        levels = [
            DownsamplingLevelDict(
                {"ratio": 1, "grid": prepared_data, "set_table": initial_set_table}
            )
        ]

        # store levels list in zarr structure (can be separate function)
        store_downsampling_levels_in_zarr(
            levels,
            segmentation_group,
            params_for_storing=params_for_storing,
            time_frame="0",
        )


    def store_segmentation_data(self,
        prepared_data: PreparedLatticeSegmentationData | PreparedMeshSegmentationData,
        segmentation_gr: zarr.Group,
        value_to_segment_id_dict_for_specific_segmentation_id: dict,
        params_for_storing: dict,
        primary_descriptor: PrimaryDescriptor
    ):
        match primary_descriptor:
            case PrimaryDescriptor.three_d_volume:
                self._store_lattice_segmentation_data(
                    prepared_data,
                    segmentation_gr,
                    value_to_segment_id_dict_for_specific_segmentation_id,
                    params_for_storing
                )
            case PrimaryDescriptor.mesh_list:
                self._store_mesh_segmentation_data(
                    segmentation_group=segmentation_gr,
                    prepared_data=prepared_data,
                    params_for_storing=params_for_storing
                )



    def get_sff_model(self):
        return self.get_sff_wrapper().data_model
    
    def _prepare_sff(self):
        w = self.get_sff_wrapper()
        self.primary_descriptor = w.data_model.primary_descriptor
        self.raw_sff_annotations = w.get_raw_annotations()
        prepared = w.process_data()
        return prepared
        
    def set_segmentation_ids_mapping(self):
        if self.custom_data.segmentation_ids_mapping is None:
            # not provided, try to get from metadata if omezarr
            match self.input_kind:
                case AssetKind.omezarr:
                    w = self.get_omezarr_wrapper()
                    self.custom_data.segmentation_ids_mapping = w.create_channel_ids_mapping()
                case AssetKind.sff:
                    w = self.get_sff_wrapper()
                    self.custom_data.segmentation_ids_mapping = w.create_segmentation_ids_mapping() 
                case AssetKind.ometiff_segmentation:
                    w = self.get_ometiff_wrapper()
                    self.custom_data.segmentation_ids_mapping = w.create_channel_ids_mapping()
                case AssetKind.mask:
                    ws = self.get_mask_wrappers()
                    list_of_dicts = [{w.path.stem: w.path.stem} for w in ws]
                    mapping = {
                        k: v for k, v in list_of_dicts
                    }
                    self.custom_data.segmentation_ids_mapping = mapping
                    
                case _:
                    raise NotImplementedError(f"{self.input_kind} not supported")
        
    def postprepare(self):
        '''
        Sets segmentation ids in prepared data; possibly other things
        '''
        
        self.prepared.metadata.segmentation_ids = list(self.custom_data.segmentation_ids_mapping.values())
        for idx, item in enumerate(self.prepared.data):
            assert item.segmentation_id is not None
            item.segmentation_id = self.custom_data.segmentation_ids_mapping[str(item.segmentation_id)]
            self.prepared.data[idx] = item
    
    def store(self):
        root = self.get_zarr_root()
        gr: zarr.Group = None
        match self.primary_descriptor:
            case PrimaryDescriptor.three_d_volume:
                gr = root.require_group(LATTICE_SEGMENTATION_DATA_GROUPNAME)
            case PrimaryDescriptor.mesh_list:
                gr = root.require_group(MESH_SEGMENTATION_DATA_GROUPNAME)
            case _:
                raise NotImplementedError()
        
        preprared_data = self.prepared.data
        
        for d in preprared_data:
            # segmentation_gr = gr.create_group(d.segmentation_id)
            self.store_segmentation_data(
                prepared_data=d,
                segmentation_gr=gr,
                value_to_segment_id_dict_for_specific_segmentation_id=self.value_to_segment_id_dict,
                params_for_storing=self.params_for_storing,
                primary_descriptor=self.primary_descriptor
            )
    
    def get_data_array(self, segmentation_kind: SegmentationKind, segmentation_id: str, resolution: int, timeframe_index: int):
        return self.get_segmentation_data_group(segmentation_kind)[f'{segmentation_id}/{resolution}/{timeframe_index}']

    # def get_data_array(self, segmentation_kind: SegmentationKind, segmentation_id: str, resolution: int, timeframe_index: int):
    #     return self.get_segmentation_data_group(segmentation_kind)[f'{segmentation_id}/{resolution}/{timeframe_index}']
    
    def get_mesh_zattrs(self, segmentation_id: str, timeframe_index: int,
                        segment_id: int, detail_lvl: int, mesh_id: int):
        # TODO: fix validation errors
        return MeshZattrs.model_validate(\
            self.get_segmentation_data_group(SegmentationKind.mesh)[segmentation_id][timeframe_index]\
                [segment_id][detail_lvl][mesh_id].attrs[MESH_ZATTRS_NAME])

        # specific for segmentation id and  timeframe group
    def set_mesh_zattrs(self, segmentation_id: str, timeframe_index: int,
                        segment_id: int, detail_lvl: int, mesh_id: int, m: MeshZattrs):
        # should be specific to segmentation
        self.get_segmentation_data_group(SegmentationKind.mesh)[segmentation_id][timeframe_index]\
                [segment_id][detail_lvl][mesh_id].attrs[MESH_ZATTRS_NAME] = m.model_dump()
    
    def prepare(self):
        match self.input_kind:
            case AssetKind.sff:
                self.prepared = self._prepare_sff()                
            case AssetKind.ometiff_segmentation:
                self.prepared = self._prepare_ometiff_segmentation()
            case AssetKind.mask:
                # for a single mask as single lattice
                self.prepared = self._prepare_mask_segmenation()
            case AssetKind.tiff_segmentation_stack_dir:
                self.prepared = self._prepare_tiff_stack_segmenation()
                
            case _:
                raise NotImplementedError(f'{self.input_kind} is not supported')

        self.value_to_segment_id_dict = self.prepared.metadata.value_to_segment_id_dict

    def set_segmentation_sampling_boxes(self):
        input_kind = self.input_kind
        self = self.get_segmentation_data_group(SegmentationKind.lattice)
        m = self.get_metadata()
        # NOTE: assumes map and sff/mask has same dimension
        # otherwise segmentation does not make sense
        if input_kind in [AssetKind.sff, AssetKind.mask, AssetKind.omezarr]:
            vboxes = m.volumes.sampling_info.boxes
            # should create info gor each lattice and resolution
            for lattice_id, lat_gr in self.groups():
                segm_resoltions = lat_gr.group_keys()
                m.segmentation_lattices.sampling_info[lattice_id] = BLANK_SAMPLING_INFO
                # for res, res_gr in lat_gr.groups():
                sboxes = {k: v for k, v in vboxes.items() if str(k) in segm_resoltions}
                # assert int(res) in vboxes, f'Resolution {res} does not exist in volume data, cannot obtain it'
                m.segmentation_lattices.sampling_info[lattice_id].boxes = sboxes
        # elif input_kind == InputKind.omezarr:
        #     pass
        else:
            raise Exception(f"Input kind {input_kind} is not recognized")
        self.set_metadata(m)

    def set_segmentation_lattices_metadata(self):
        data_gr = self.get_segmentation_data_group(SegmentationKind.lattice)
        m = self.get_metadata()
        if self.input_kind == AssetKind.sff:
            original_axis_order = [AxisName.x, AxisName.y, AxisName.z]
        elif self.input_kind in [AssetKind.omezarr, AssetKind.tiff_segmentation_stack_dir]:
            original_axis_order = m.volumes.sampling_info.original_axis_order
        else:
            raise Exception(f"{self.input_kind} is not supported")

        # m.segmentation_lattices.ids = []
        for lattice_id, lattice_gr in data_gr.groups():
            downsamplings = get_downsamplings(data_group=lattice_gr)
            m.segmentation_lattices.ids.append(lattice_id)

            sampling_info = SamplingInfo(
                spatial_downsampling_levels=downsamplings,
                boxes={},
                time_transformations=[],
                original_axis_order=original_axis_order,
            )
            m.segmentation_lattices.sampling_info[lattice_id] = sampling_info
            m.segmentation_lattices.time_info_mapping[lattice_id] = TIME_INFO_STANDARD

        # till here

        self.set_segmentation_sampling_boxes()
        self.set_metadata(m)

    def set_meshes_metadata(self):
        s = self.get_segmentation_data_group(SegmentationKind.mesh)

        m = self.get_metadata()
        mesh_set_metadata = MeshesMetadata(
            detail_lvl_to_fraction=self.simplification_curve,
            mesh_timeframes={},
        )
        # should be not attr of group but of array
        # currently set to attrs of mesh_id group
        # 
        # should use just that segmentation id
        segmentation_ids: list[str] = []
        for segmentation_id, segmentation_gr in s.groups():
            for timeframe_index, timeframe_gr in segmentation_gr.groups():
                mesh_comp_num = MeshComponentNumbers(segment_ids={})
                for segment_id, segment in timeframe_gr.groups():
                    detail_lvls_metadata = DetailLvlsMetadata(detail_lvls={})
                    for detail_lvl, detail_lvl_gr in segment.groups():
                        mesh_list_metadata = MeshListMetadata(mesh_ids={})
                        for mesh_id, mesh in detail_lvl_gr.groups():
                            # mesh_metadata: MeshMetadata = {}
                            temp_m = {}
                            # num vertices none
                            for mesh_component_name, mesh_component in mesh.arrays():
                                temp_m[f"num_{mesh_component_name}"] = (
                                    mesh.attrs[MESH_ZATTRS_NAME][f"num_{mesh_component_name}"]
                                )
                            mm = MeshMetadata(
                                num_normals=temp_m.get("num_normals", None),
                                num_triangles=temp_m["num_triangles"],
                                num_vertices=temp_m["num_vertices"],
                            )
                            mesh_list_metadata.mesh_ids[int(mesh_id)] = mm
                        detail_lvls_metadata.detail_lvls[int(detail_lvl)] = (
                            mesh_list_metadata
                        )
                    mesh_comp_num.segment_ids[int(segment_id)] = detail_lvls_metadata
                mesh_set_metadata.mesh_timeframes[int(timeframe_index)] = mesh_comp_num

            m.segmentation_meshes.metadata[segmentation_id] = mesh_set_metadata
            # rather overwrite here
            segmentation_ids.append(segmentation_id)
            m.segmentation_meshes.time_info_mapping[segmentation_id] = TIME_INFO_STANDARD
            
        m.segmentation_meshes.ids = segmentation_ids
        # on second iteration actin_downsized_is_duplicated in metadata
        # no time info mapping, no ids
        self.set_metadata(m)

    def set_custom_data(self):
        r = self.get_zarr_root()
        
        
        # need to set it artificially if not provided 
        # list_of_sesgmentation_pathes: list[Path] = s.input_path
        # s.custom_data["segmentation_ids_mapping"] = {
        #     s.stem: s.stem for s in list_of_sesgmentation_pathes
        # }
        if "extra_data" in r.attrs:
            if "segmentation" in r.attrs["extra_data"]:
                self.custom_data = SegmentationExtraData.model_validate(r.attrs["extra_data"]["segmentation"])
            else:
                self.custom_data = SegmentationExtraData()
        else:
            self.custom_data = SegmentationExtraData()
