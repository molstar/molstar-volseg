from pydantic.dataclasses import dataclass
import gc
from pathlib import Path
from typing import Any

from pyometiff import OMETIFFReader
import zarr
from cellstar_db.models import (
    AxisName,
    DimensionSizes,
    OMETIFFMetadata,
    OMEZarrAttrs,
    PreparedLatticeSegmentationData,
    PreparedSegmentation,
    PreparedSegmentationMetadata,
    PreparedVolume,
    PreparedVolumeData,
    PreparedVolumeMetadata,
    SegmentationKind,
    SpatialAxisUnit,
    TimeAxisUnit,
    TimeTransformation,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
import bfio
# OMEZARR_AXIS_NUMBER_TO_NAME_ORDER = {
#     0:
# }
import dask.array as da

def ometiff_to_reader_bfio(path: Path):
    '''
    Order: XYZ, channel, time 
    '''
    # Initialize the bioreader
    br = bfio.BioReader(path, backend="bioformats")
    return br

@dataclass
class OMETIFFWrapper:
    path: Path
    # data5D: da.Array | None = None
    
    # metadata: OMETIFFMetadata | None
    # xml_metadata: str | None
    # _order: str = "TZCYX"
    # _correct_order: str = "TCXYZ"
    # def __post_init__(self):
    #     self._add_missing_dims()
    #     self.data: da.Array = 
    
    @property
    def _dimensions_dict(self):
        return {
            AxisName.x: 0,
            AxisName.y: 1,
            AxisName.z: 2,
            AxisName.c: 3,
            AxisName.t: 4,
        }
    
    @property
    def reader(self):
        # does not exist here
        return ometiff_to_reader_bfio(self.path)
        # self.reader = r
    # def __post_init__(self):
        # self.data, self.metadata, self.xml_metadata = read_ometiff_pyometiff(self.path)
        # if self._order is None:
        #     self._order = "TZCYX"

    def create_channel_ids_mapping(self):
        m: dict[str, str] = {}
        # do sequential
        if self.channels is not None:
            for idx, channel_name in enumerate(self.channels):
                # NOTE: assuming order of channels is the same as in data               
                m[str(idx)] = channel_name
                
        else:
            for channel_num in self.channel_numbers:
                m[str(channel_num)] = str(channel_num)
    
        return m
    
    def add_missing_dims(self):
        missing_dims = self.missing_dims
        for dim in missing_dims:
            data = da.expand_dims(self.raw_data, axis=self._dimensions_dict[dim])
        return data
    
    @property
    def data(self):
        return self.add_missing_dims() 
        # order = metadata["DimOrder BF Array"]
        # for letter in order:
        #     d[str(letter)] = order.index(str(letter))

        # missing_dims = []

        # if len(img_array.shape) != 5:
        #     missing_dims = _get_missing_dims(metadata["Sizes BF"])
        #     for missing_dim in missing_dims:
        #         img_array = da.expand_dims(img_array, axis=d[missing_dim])

        # CORRECT_ORDER = "TCXYZ"
        # reorder_tuple = _create_reorder_tuple(d, CORRECT_ORDER)
        # # NOTE: assumes correct order is TCXYZ

        # i.custom_data

        # rearranged_arr = img_array.transpose(*reorder_tuple)

        # artificial_channel_ids = list(range(rearranged_arr.shape[1]))
        # artificial_channel_ids = [str(x) for x in artificial_channel_ids]
        # # TODO: prepare list of of PreparedOMETIFFData
        # # for each time and channel
        # for time in range(rearranged_arr.shape[0]):
        #     time_arr = rearranged_arr[time]
        #     for channel_number in range(time_arr.shape[0]):
        #         three_d_arr = time_arr[channel_number]
        #         p = PreparedOMETIFFData(
        #             channel_number=channel_number,
        #             timeframe_index=time,
        #             data=three_d_arr,
        #         )
        #         prepared_data.append(p)

        # artificial_channel_ids_dict = dict(
        #     zip(artificial_channel_ids, artificial_channel_ids)
        # )
        # return prepared_data, artificial_channel_ids_dic
    
    
    @property
    def raw_data(self):
        '''Order: XYZCT'''
        np_arr = self.reader.read()
        dask_arr = da.from_array(np_arr)
        del np_arr
        gc.collect()
        return dask_arr
    
    @property
    def raw_dimensionality(self):
        '''Number of dimensions in data istelf'''
        return len(self.raw_data.shape)
    
    @property
    def dimensions(self):
        # pydantic, attr names = x, y, z, values .X .Y. Z. etc
        # can reuse axis names?
        dims = DimensionSizes(
            X=self.reader.X,
            Y=self.reader.Y,
            Z=self.reader.Z,
            C=self.reader.C,
            T=self.reader.T,
        )
        return dims
    
    @property
    def timeframe_indices(self):
        return list(range(0, self.dimensions.T))
    
    @property
    def channel_numbers(self):
        return list(range(0, self.dimensions.C))

    @property
    def segmentation_numbers(self):
        return self.channel_numbers
    
    @property
    def segmentation_ids(self):
        return [str(i) for i in self.segmentation_numbers]
    
    
    @property
    def missing_dims(self):
        missing_dims: list[AxisName]  = []
        match self.raw_dimensionality:
            case 4:
                # XYZC
                if len(self.reader.cnames) > 0:
                    missing_dims.append(AxisName.t)
                else:
                    raise NotImplementedError('Support for XYZT has not been implemented yet')
            case 3:
                raise NotImplementedError('Support for XYZ has not been implemented yet')

        return missing_dims
    # def 
    
    def get_spatial_data(self, channel_number: int, timeframe_index: int):
        # data = self.data
        # return data[:,:,:, channel_number: (channel_number + 1), timeframe_index: (timeframe_index + 1)]
        
        
        
        # I = br.read(X=[0,100],Y=[0,100])
        # TODO: T = list from + 1
        # T=[0,0] works
        # return self.reader.read(T=[timeframe_index, timeframe_index + 1], C=[channel_number, channel_number + 1])
        # NOTE: channel - lattice
        np_arr = self.reader[:,:,:, channel_number: (channel_number + 1), timeframe_index: (timeframe_index + 1)]
        dask_arr = da.from_array(np_arr)
        del np_arr
        gc.collect()
        return dask_arr
        # TODO: implement my own
        # 1. Extend missing dims
        # Now for sure that the order is XYZCT
        # DEFAULT_AXIS_ORDER_5D
        # if something is missing it is not there
        # we will expand it artificially
        
        
        
        
        
    @property
    def metadata(self):
        return self.reader.metadata
    
    @property
    # can be not provided
    def channels(self):
        actual: list[str] = []
        cnames = self.reader.cnames
        for idx, channel_name in enumerate(cnames):
            # NOTE: assuming order of channels is the same as in data
            if channel_name == '(name not specified)':
                actual.append(str(self.channel_numbers[idx]))
            else:
                actual.append(str(cnames[idx]))
        
        return actual
    
    
        
    # def _create_reorder_tuple(self):
    #     reorder_tuple = tuple([d[l] for l in correct_order])
    #     return reorder_tuple
      
    # def _get_missing_dims(self):
    #     sizesBFcorrected = self.metadata.SizesBF[1:]
    #     missing: str = []
    #     for idx, dim in enumerate(sizesBFcorrected):
    #         if dim == 1:
    #             missing.append(self._order[idx])
    #     print(f"Missing dims: {missing}")
    #     return missing

    # def _get_ometiff_axis_order(self):
    #     str_order = self.metadata.DimOrderBFArray
    
    def prepare_volume_data(self) -> PreparedVolume:
        # channel_nums: list[int] = []
        # local_timeframe_indices: list[int] = []
        resolutions: list[int]= []
        l: list[PreparedVolumeData] = []
        
        resolution = 1
        resolutions.append(resolution)
        for timeframe_index in self.timeframe_indices:
            # timeframe_indices.append(timeframe_index)
            for channel_number in self.channel_numbers:
                data = self.get_spatial_data(timeframe_index=timeframe_index, channel_number=channel_number)
                # data = self.data[timeframe_index][channel_num]

                l.append(
                    PreparedVolumeData(
                        timeframe_index=timeframe_index,
                        channel_num=channel_number,
                        data=data,
                        resolution=resolution,
                        nbytes=data.nbytes
                    )
                )

                # channel_nums.append(channel_num)
                gc.collect()
        # TODO: 4D case?
            # elif len(axes) == 4 and axes[0].name == AxisName.c:
            #     timeframe_indices.append(0)
            #     for channel_num in range(self.data5D.shape[0]):
            #         data = da.from_zarr(self.data5D)[channel_num].swapaxes(0, 2)
            #         l.append(
            #                 PreparedVolumeData(
            #                     timeframe_index='0',
            #                     channel_num=channel_num,
            #                     data=data,
            #                     resolution=resolution,
            #                     size=data.nbytes
            #                 )
            #             )
            #         channel_nums.append(channel_num)
            #         gc.collect()
            # else:
            #     raise Exception(f"Axes number/order {axes} is not supported")
        
        p = PreparedVolume(
            data=l,
            metadata=PreparedVolumeMetadata(
                channel_nums=self.channel_numbers,
                timeframe_indices=self.timeframe_indices,
                resolutions=resolutions
            )
        )
        return p

    def prepare_segmentation_data(self) -> PreparedSegmentation:
        value_to_segment_id_dict: dict[str, str] = {}
        # channel_nums: list[int] = []
        # local_timeframe_indices: list[int] = []
        resolutions: list[int]= []
        l: list[PreparedLatticeSegmentationData] = []
        
        resolution = 1
        resolutions.append(resolution)
        for timeframe_index in self.timeframe_indices:
            # timeframe_indices.append(timeframe_index)
            for segmentation_id in self.segmentation_ids:
                value_to_segment_id_dict[segmentation_id] = {}
                # segmentation_id = str(segmentation_id)
                data = self.get_spatial_data(timeframe_index=timeframe_index, channel_number=int(segmentation_id))
                # data = self.data[timeframe_index][channel_num]

                l.append(
                    PreparedLatticeSegmentationData(
                        timeframe_index=timeframe_index,
                        segmentation_id=segmentation_id,
                        data=data,
                        resolution=resolution,
                        nbytes=data.nbytes
                    )
                )
                for value in da.unique(data).compute():
                    value_to_segment_id_dict[segmentation_id][int(value)] = int(value) 

                # channel_nums.append(channel_num)
                gc.collect()
        # TODO: 4D case?
            # elif len(axes) == 4 and axes[0].name == AxisName.c:
            #     timeframe_indices.append(0)
            #     for channel_num in range(self.data5D.shape[0]):
            #         data = da.from_zarr(self.data5D)[channel_num].swapaxes(0, 2)
            #         l.append(
            #                 PreparedVolumeData(
            #                     timeframe_index='0',
            #                     channel_num=channel_num,
            #                     data=data,
            #                     resolution=resolution,
            #                     size=data.nbytes
            #                 )
            #             )
            #         channel_nums.append(channel_num)
            #         gc.collect()
            # else:
            #     raise Exception(f"Axes number/order {axes} is not supported")
        
        p = PreparedSegmentation(
            data=l,
            metadata=PreparedSegmentationMetadata(
                segmentation_ids=self.segmentation_ids,
                timeframe_indices=self.timeframe_indices,
                resolutions=resolutions,
                value_to_segment_id_dict=value_to_segment_id_dict
            ),
            kind=SegmentationKind.lattice
        )
        return p

def read_ometiff_pyometiff(path: Path):
    reader = OMETIFFReader(fpath=path)
    img_array_np, metadata, xml_metadata = reader.read()
    img_array = da.from_array(img_array_np)
    del img_array_np
    gc.collect()
    return img_array, metadata, xml_metadata
    
    # def get_image_resolutions(self):
    #     r_str = self.get_image_group().array_keys()
    #     return sorted([int(r) for r in r_str])

    # def get_label_resolutions(self, label_name: str):
    #     r_str = self.get_labels_group()[label_name].group_keys()
    #     return sorted([int(r) for r in r_str])

    # def get_image_group(self):
    #     return open_zarr(self.path)

    # def get_labels_group(self) -> zarr.Group:
    #     return self.get_image_group().labels

    # def get_label_names(self):
    #     return list(self.get_labels_group().group_keys())

    # def get_image_zattrs(self):
    #     return OMEZarrAttrs.model_validate(self.get_image_group().attrs)

    # def get_label_zattrs(self, label_name: str):
    #     return OMEZarrAttrs.model_validate(self.get_labels_group()[label_name].attrs)

    # def get_image_multiscale(self):
    #     """Only the first multiscale"""
    #     # NOTE: can be multiple multiscales, here picking just 1st
    #     return self.get_image_zattrs().multiscales[0]

    # def get_label_multiscale(self, label_name: str):
    #     """Only the first multiscale"""
    #     # NOTE: can be multiple multiscales, here picking just 1st
    #     return self.get_label_zattrs(label_name).multiscales[0]

    # def get_axes(self):
    #     """Root level axes, not present in majority of used OMEZarrs"""
    #     raise NotImplementedError()

    # def get_omero_channels(self):
    #     # should check if exists, if not - return so
    #     if self.get_image_zattrs().omero:
    #         if self.get_image_zattrs().omero.channels: 
    #             return self.get_image_zattrs().omero.channels
            
    #     return None

    # def get_time_units(self):
    #     m = self.get_image_multiscale()
    #     axes = m.axes
    #     t_axis = axes[0]
    #     # change to ax
    #     if t_axis.name == AxisName.t:
    #         if t_axis.unit is not None:
    #             return t_axis.unit
    #     # if first axes is not time
    #     return TimeAxisUnit.millisecond

    # def set_zattrs(self, new_zattrs: dict[str, Any]):
    #     root = self.get_image_group()
    #     root.attrs.put(new_zattrs)
    #     print(f"New zattrs: {root.attrs}")

    # def add_defaults_to_ome_zarr_attrs(self):
    #     zattrs = self.get_image_zattrs()
    #     axes = zattrs.multiscales[0].axes
    #     for axis in axes:
    #         if axis.unit is None:
    #             # if axis.type is not None:
    #             if axis.name in [AxisName.x, AxisName.y, AxisName.z]:
    #                 axis.unit = SpatialAxisUnit.angstrom
    #             elif axis.name == AxisName.t:
    #                 axis.unit = TimeAxisUnit.millisecond

    #     self.set_zattrs(zattrs.model_dump())

    # def process_time_transformations(self):
    #     # NOTE: can be multiple multiscales, here picking just 1st
    #     time_transformations_list: list[TimeTransformation] = []
    #     multiscales = self.get_image_multiscale()
    #     axes = multiscales.axes
    #     datasets_meta = multiscales.datasets
    #     first_axis = axes[0]
    #     if first_axis.name == AxisName.t:
    #         for idx, level in enumerate(datasets_meta):
    #             assert (
    #                 level.coordinateTransformations[0].scale is not None
    #             ), "OMEZarr should conform to v4 specification with scale"
    #             scale_arr = level.coordinateTransformations[0].scale
    #             if len(scale_arr) == 5:
    #                 factor = scale_arr[0]
    #                 if multiscales.coordinateTransformations is not None:
    #                     if multiscales.coordinateTransformations[0].type == "scale":
    #                         factor = (
    #                             factor
    #                             * multiscales.coordinateTransformations[0].scale[0]
    #                         )
    #                 time_transformations_list.append(
    #                     TimeTransformation(downsampling_level=level.path, factor=factor)
    #                 )
    #             else:
    #                 raise Exception("Length of scale arr is not supported")

    #         return time_transformations_list
    #     else:
    #         return time_transformations_list
