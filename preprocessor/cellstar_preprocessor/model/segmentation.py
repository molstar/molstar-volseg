from dataclasses import dataclass, field
import gc
from typing import Any
from cellstar_preprocessor.flows.segmentation.category_set_downsampling_methods import store_downsampling_levels_in_zarr
import dask.array as da
import zarr
from cellstar_db.models import (
    AxisName,
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
    PreparedMeshSegmentationData,
    PreparedSegmentation,
    SamplingInfo,
    SegmentationExtraData,
    SegmentationKind,
    SegmentationPrimaryDescriptor,
    SegmentationSetTable,
    StoringParams,
)
from cellstar_preprocessor.flows.constants import (
    BLANK_SAMPLING_INFO,
    LATTICE_SEGMENTATION_DATA_GROUPNAME,
    MESH_SEGMENTATION_DATA_GROUPNAME,
    MESH_ZATTRS_NAME,
    TIME_INFO_STANDARD,
    VOLUME_DATA_GROUPNAME,
)
# from cellstar_preprocessor.flows.segmentation.helper_methods import hdf5_to_zarr
from cellstar_preprocessor.flows.zarr_methods import create_dataset_wrapper, get_downsamplings
from cellstar_preprocessor.model.internal_data import InternalData
from cellstar_preprocessor.model.sff import SFFWrapper


@dataclass
class InternalSegmentation(InternalData):
    custom_data: SegmentationExtraData | None = None
    primary_descriptor: SegmentationPrimaryDescriptor | None = None
    value_to_segment_id_dict: dict = field(default_factory=dict)
    simplification_curve: dict[int, float] = field(default_factory=dict)
    raw_sff_annotations: dict[str, Any] = field(default_factory=object)
    map_headers: dict[str, object] = field(default_factory=dict)
    prepared: PreparedSegmentation | None = None
    
    
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

        time_group: zarr.Group = segmentation_group.create_group(
            f"{segmentation_id}/{0}/{0}"
        )

        for d in prepared_data.mesh_list:
            # vertices = d.vertices
            # triangles = d.triangles
            # normals = d.normals
            area = d.area
            segment_id = str(d.segment_id)
            mesh_id = str(d.mesh_id)
            segment_gr = time_group.require_group(segment_id)
            detail_lvl_gr = segment_gr.require_group('1')
            mesh_gr = detail_lvl_gr.require_group(mesh_id)



            # print(getattr(Color, color_name).value)
            # TODO: optimize to loop

            for e in MeshElementName:
                name = e.name
                # value = e.value
                element_array: da.Array = getattr(d, name)
                create_dataset_wrapper(
                    zarr_group=mesh_gr,
                    data=element_array,
                    name=name,
                    shape=element_array.shape,
                    dtype=element_array.dtype,
                )
                w = self.get_mesh_zattrs()
                num_element_name = f"num_{name}"
                setattr(w, num_element_name, element_array.size)

                w.area = area


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
        primary_descriptor: SegmentationPrimaryDescriptor
    ):
        match primary_descriptor:
            case SegmentationPrimaryDescriptor.three_d_volume:
                self._store_lattice_segmentation_data(
                    prepared_data,
                    segmentation_gr,
                    value_to_segment_id_dict_for_specific_segmentation_id,
                    params_for_storing
                )
            case SegmentationPrimaryDescriptor.mesh_list:
                self._store_mesh_segmentation_data(
                    prepared_data,
                    segmentation_gr,
                    params_for_storing
                )



        
    def get_sff_wrapper(self):
        return SFFWrapper(self.input_path)
    
    def get_sff_model(self):
        return self.get_sff_wrapper().data_model
    
    def _prepare_sff(self):
        # hdf5_to_zarr(self)
        # root = self.get_zarr_root()
        root = self.get_zarr_root()
        
        
        w = self.get_sff_wrapper()
        self.raw_sff_annotations = w.get_raw_annotations()

        # # PLAN:
        # # 1. Convert hff to intermediate zarr structure
        # # 2. Process it with one of 2 methods (3d volume segmentation, mesh segmentation)
        
        # 1. check descriptor
        # primary_descriptor = w.data_model.primary_descriptor
        
        # match primary_descriptor:
            # case SegmentationPrimaryDescriptor.three_d_volume:
        # self.primary_descriptor = (
        #     SegmentationPrimaryDescriptor.three_d_volume
        # )
        
        # map value to segment id as separate function
        # self.value_to_segment_id_dict = w.map_value_to_segment_id()
        w.process_data()

            # case SegmentationPrimaryDescriptor.mesh_list:
            #     pass
            # case SegmentationPrimaryDescriptor.shape_primitive_list:
            #     raise NotImplementedError()
            # case _:
            #     raise ValueError()
        
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

    def set_segmentation_ids_mapping(self):
        if self.custom_data.segmentation_ids_mapping is None:
            # not provided, try to get from metadata if omezarr
            if self.input_kind == AssetKind.omezarr:
                raise NotImplementedError(f"{self.input_kind} not supported")
                # w = self.get_omezarr_wrapper()
                # self.custom_data.channel_ids_mapping = w.create_channel_ids_mapping()
            elif self.input_kind == AssetKind.sff:
                # get channel ids
                w = self.get_sff_wrapper()
                self.custom_data.segmentation_ids_mapping = w.create_segmentation_ids_mapping() 
            elif self.input_kind == AssetKind.ometiff_image:
                raise NotImplementedError(f"{self.input_kind} not supported")
                # w = self.get_ometiff_wrapper()
                # self.custom_data.channel_ids_mapping = w.create_channel_ids_mapping()
            else:
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
            case SegmentationPrimaryDescriptor.three_d_volume:
                gr = root.create_group(LATTICE_SEGMENTATION_DATA_GROUPNAME)
            case SegmentationPrimaryDescriptor.mesh_list:
                gr = root.create_group(MESH_SEGMENTATION_DATA_GROUPNAME)
            case _:
                raise NotImplementedError()
        
        preprared_data = self.prepared.data
        
        for d in preprared_data:
            segmentation_gr = gr.create_group(d.segmentation_id)
            self.store_segmentation_data(
                prepared_data=d,
                segmentation_gr=segmentation_gr,
                value_to_segment_id_dict_for_specific_segmentation_id=self.value_to_segment_id_dict,
                params_for_storing=self.params_for_storing,
                primary_descriptor=self.primary_descriptor
            )
    
    def remove_downsamplings(self):
        # TODO: remove original resolution for meshes?
        m = self.get_metadata()
        match self.primary_descriptor:
            case SegmentationPrimaryDescriptor.three_d_volume:
                segmentation_gr = self.get_segmentation_data_group(SegmentationKind.lattice)
                for lattice_id in m.segmentation_lattices.ids:
                    lattice_gr = segmentation_gr[lattice_id]
                    original_resolution = self.get_first_resolution_group(lattice_gr)
                    for info in get_downsamplings(lattice_gr):
                        if info.available:
                            res = info.level
                        else:
                            continue
                        size_of_data_for_lvl_mb = self.prepared.compute_size_for_downsampling_level(res)
                        print(f"size of data for lvl in mb: {size_of_data_for_lvl_mb}")
                        if (
                            (self.downsampling_parameters.max_size_per_downsampling_lvl_mb
                            and size_of_data_for_lvl_mb
                            > self.downsampling_parameters.max_size_per_downsampling_lvl_mb)
                            or
                            (
                                self.downsampling_parameters.min_size_per_downsampling_lvl_mb
                                and size_of_data_for_lvl_mb < self.downsampling_parameters.min_size_per_downsampling_lvl_mb
                            )
                        ):
                            print(f"Segmentation data for resolution {res} was removed")
                            del lattice_gr[res]
                            gc.collect()
                        
                        if self.downsampling_parameters.max_downsampling_level is not None:
                            for downsampling, downsampling_gr in lattice_gr.groups():
                                if int(downsampling) > self.downsampling_parameters.max_downsampling_level:
                                    del lattice_gr[downsampling]
                                    gc.collect()
                                    print(f"Data for downsampling {downsampling} removed for volume")

                        if self.downsampling_parameters.min_downsampling_level is not None:
                            for downsampling, downsampling_gr in lattice_gr.groups():
                                if (
                                    int(downsampling) < self.downsampling_parameters.min_downsampling_level
                                    and downsampling != original_resolution
                                ):
                                    del lattice_gr[downsampling]
                                    gc.collect()
                                    print(f"Data for downsampling {downsampling} removed for volume")

                        if len(sorted(lattice_gr.group_keys())) == 0:
                            raise Exception(
                                f"No downsamplings will be saved: max_size_per_downsampling_lvl_mb {self.downsampling_parameters.max_size_per_downsampling_lvl_mb} is too low"
                            )
            case SegmentationPrimaryDescriptor.mesh_list:
                raise NotImplementedError()
            case _:
                raise ValueError()
            
        
    
    def remove_original_resolution(self):
        m = self.get_metadata()
        if self.downsampling_parameters.remove_original_resolution:
            segm_data_gr: zarr.Group = self.get_segmentation_data_group()
            for lattice_id in m.segmentation_lattices.ids:
                first_resolution = str(segm_data_gr.name)
                del segm_data_gr[first_resolution]
                print(f"Original resolution ({first_resolution}) for segmentation data removed")

                current_levels = m.segmentation_lattices.sampling_info[lattice_id].spatial_downsampling_levels
        
                for i, item in enumerate(current_levels):
                    if item.level == first_resolution:
                        current_levels[i].available = False
                # fix metadata
                m.segmentation_lattices.sampling_info[lattice_id].spatial_downsampling_levels = current_levels
            
        self.set_metadata(m)
    

    def get_mesh_zattrs(self):
        return MeshZattrs.model_validate(self.get_zarr_root().attrs[MESH_ZATTRS_NAME])
    
    def set_mesh_zattrs(self, m: MeshZattrs):
        self.get_zarr_root().attrs[MESH_ZATTRS_NAME] = m.model_dump()
    
    def prepare(self):
        match self.input_kind:
            case AssetKind.sff:
                self._prepare_sff()
                
            case AssetKind.ometiff_segmentation:
                raise NotImplementedError(f'{self.input_kind} is not supported')
                # w = self.get_omezarr_wrapper()
                # self.prepared = w.prepare_volume_data()
            # case AssetKind.ometiff_image: 
            #     self.prepared = self.prepare_ometiff()
            # case AssetKind.map:
            #     self.prepared = self.prepare_map()
                
            case _:
                raise NotImplementedError(f'{self.input_kind} is not supported')
    def set_segmentation_sampling_boxes(self):
        input_kind = self.input_kind
        s = self.get_segmentation_data_group(SegmentationKind.lattice)
        m = self.get_metadata()
        # NOTE: assumes map and sff/mask has same dimension
        # otherwise segmentation does not make sense
        if input_kind in [AssetKind.sff, AssetKind.mask, AssetKind.omezarr]:
            vboxes = m.volumes.sampling_info.boxes
            # should create info gor each lattice and resolution
            for lattice_id, lat_gr in s.groups():
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
                            for mesh_component_name, mesh_component in mesh.arrays():
                                temp_m[f"num_{mesh_component_name}"] = (
                                    mesh_component.attrs[f"num_{mesh_component_name}"]
                                )
                            mm = MeshMetadata(
                                num_normals=temp_m["num_normals"],
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

        self.set_metadata(m)

    def set_custom_data(self):
        r = self.get_zarr_root()
        if "extra_data" in r.attrs:
            if "segmentation" in r.attrs["extra_data"]:
                self.custom_data = SegmentationExtraData.model_validate(r.attrs["extra_data"]["segmentation"])
            else:
                self.custom_data = SegmentationExtraData()
        else:
            self.custom_data = SegmentationExtraData()
