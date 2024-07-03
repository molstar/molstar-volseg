import asyncio
import logging
import shutil
import typing
from argparse import ArgumentError
from pathlib import Path

from cellstar_preprocessor.flows.segmentation.extract_tiff_segmentation_stack_dir_metadata import extract_tiff_segmentation_stack_dir_metadata
from cellstar_preprocessor.flows.segmentation.tiff_segmentation_stack_dir_processing import tiff_segmentation_stack_dir_processing
from cellstar_preprocessor.flows.volume.extract_tiff_image_stack_dir_metadata import extract_tiff_image_stack_dir_metadata
from cellstar_preprocessor.flows.volume.pre_downsample_data import pre_downsample_data
from cellstar_preprocessor.flows.volume.tiff_image_processing import tiff_image_stack_dir_processing
import typer
import zarr
from cellstar_db.file_system.annotations_context import AnnnotationsEditContext
from cellstar_db.file_system.db import FileSystemVolumeServerDB
from cellstar_db.file_system.volume_and_segmentation_context import (
    VolumeAndSegmentationContext,
)
from cellstar_db.models import (
    DescriptionData,
    DownsamplingParams,
    EntryData,
    ExtraMetadata,
    GeometricSegmentationData,
    InputKind,
    Inputs,
    PreprocessorArguments,
    PreprocessorInput,
    PreprocessorMode,
    RawInput,
    SegmentAnnotationData,
    StoringParams,
    VolumeParams,
)
from cellstar_preprocessor.flows.common import process_extra_data, read_json
from cellstar_preprocessor.flows.constants import (
    GEOMETRIC_SEGMENTATIONS_ZATTRS,
    INIT_ANNOTATIONS_MODEL,
    INIT_METADATA_MODEL,
    LATTICE_SEGMENTATION_DATA_GROUPNAME,
    MESH_SEGMENTATION_DATA_GROUPNAME,
    RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS,
    VOLUME_DATA_GROUPNAME,
)
from cellstar_preprocessor.flows.segmentation.custom_annotations_preprocessing import (
    custom_annotations_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.geometric_segmentation_annotations_preprocessing import (
    geometric_segmentation_annotations_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.geometric_segmentation_metadata_preprocessing import (
    geometric_segmentation_metadata_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.geometric_segmentation_preprocessing import (
    geometric_segmentation_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.mask_segmentation_annotations_preprocessing import (
    mask_segmentation_annotations_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.mask_segmentation_metadata_preprocessing import (
    mask_segmentation_metadata_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.mask_segmentation_preprocessing import (
    mask_segmentation_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.nii_segmentation_downsampling import (
    nii_segmentation_downsampling,
)
from cellstar_preprocessor.flows.segmentation.nii_segmentation_metadata_preprocessing import (
    nii_segmentation_metadata_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.nii_segmentation_preprocessing import (
    nii_segmentation_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.ometiff_segmentation_annotations_preprocessing import (
    ometiff_segmentation_annotations_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.ometiff_segmentation_metadata_preprocessing import (
    ometiff_segmentation_metadata_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.ometiff_segmentation_processing import (
    ometiff_segmentation_processing,
)
from cellstar_preprocessor.flows.segmentation.omezarr_segmentations_preprocessing import (
    omezarr_segmentations_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.process_segmentation import (
    process_segmentation,
)
from cellstar_preprocessor.flows.segmentation.process_segmentation_annotations import (
    process_segmentation_annotations,
)
from cellstar_preprocessor.flows.segmentation.process_segmentation_metadata import (
    process_segmentation_metadata,
)
from cellstar_preprocessor.flows.segmentation.segmentation_downsampling import (
    segmentation_downsampling,
)
from cellstar_preprocessor.flows.segmentation.sff_segmentation_annotations_preprocessing import (
    sff_segmentation_annotations_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.sff_segmentation_metadata_preprocessing import (
    sff_segmentation_metadata_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.sff_segmentation_preprocessing import (
    sff_segmentation_preprocessing,
)
from cellstar_preprocessor.flows.volume.map_volume_metadata_preprocessing import (
    map_volume_metadata_preprocessing,
)
from cellstar_preprocessor.flows.volume.map_volume_preprocessing import (
    map_volume_preprocessing,
)
from cellstar_preprocessor.flows.volume.nii_volume_metadata_preprocessing import (
    nii_volume_metadata_preprocessing,
)
from cellstar_preprocessor.flows.volume.nii_volume_preprocessing import (
    nii_volume_preprocessing,
)
from cellstar_preprocessor.flows.volume.ometiff_volume_annotations_preprocessing import (
    ometiff_volume_annotations_preprocessing,
)
from cellstar_preprocessor.flows.volume.ometiff_volume_metadata_preprocessing import (
    ometiff_volume_metadata_preprocessing,
)
from cellstar_preprocessor.flows.volume.ometiff_volume_preprocessing import (
    ometiff_volume_preprocessing,
)
from cellstar_preprocessor.flows.volume.omezarr_volume_annotations_preprocessing import (
    omezarr_volume_annotations_preprocessing,
)
from cellstar_preprocessor.flows.volume.omezarr_volume_metadata_preprocessing import (
    omezarr_volume_metadata_preprocessing,
)
from cellstar_preprocessor.flows.volume.omezarr_volume_preprocessing import (
    omezarr_volume_preprocessing,
)
from cellstar_preprocessor.flows.volume.process_allencel_metadata_csv import (
    process_allencell_metadata_csv,
)
from cellstar_preprocessor.flows.volume.process_volume import process_volume
from cellstar_preprocessor.flows.volume.process_volume_annotations import (
    process_volume_annotations,
)
from cellstar_preprocessor.flows.volume.process_volume_metadata import (
    process_volume_metadata,
)
from cellstar_preprocessor.flows.volume.quantize_internal_volume import (
    quantize_internal_volume,
)
from cellstar_preprocessor.flows.volume.volume_downsampling import volume_downsampling
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.model.volume import InternalVolume
from cellstar_preprocessor.tools.convert_app_specific_segm_to_sff.convert_app_specific_segm_to_sff import (
    convert_app_specific_segm_to_sff,
)

from pydantic import BaseModel


class InputT(BaseModel):
    path: Path | list[Path]
    kind: InputKind

class TIFFImageStackDirInput(InputT):
    pass

class TIFFSegmentationStackDirInput(InputT):
    pass 

class OMETIFFImageInput(InputT):
    pass


class OMETIFFSegmentationInput(InputT):
    pass


class ExtraDataInput(InputT):
    pass


class MAPInput(InputT):
    pass


class SFFInput(InputT):
    pass


class OMEZARRInput(InputT):
    pass


class CustomAnnotationsInput(InputT):
    pass


class NIIVolumeInput(InputT):
    pass


class NIISegmentationInput(InputT):
    pass


class MaskInput(InputT):
    pass


class GeometricSegmentationInput(InputT):
    pass


class TaskBase(typing.Protocol):
    def execute(self) -> None: ...


class CustomAnnotationsCollectionTask(TaskBase):
    # NOTE: for this to work, custom annotations json must contain only the keys that
    # need to be updated
    def __init__(
        self, input_path: Path, intermediate_zarr_structure_path: Path
    ) -> None:
        self.input_path = input_path
        self.intermediate_zarr_structure_path = intermediate_zarr_structure_path

    def execute(self) -> None:
        custom_annotations_preprocessing(
            self.input_path, self.intermediate_zarr_structure_path
        )


class QuantizeInternalVolumeTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        quantize_internal_volume(internal_volume=self.internal_volume)


VOLUME_INPUT_TYPES = (MAPInput, OMETIFFImageInput, OMEZARRInput, TIFFImageStackDirInput)

SEGMENTATION_INPUT_TYPES = (
    SFFInput,
    MaskInput,
    GeometricSegmentationInput,
    OMETIFFSegmentationInput,
    OMEZARRInput,
    TIFFSegmentationStackDirInput
)


class SFFAnnotationCollectionTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        annotations_dict = sff_segmentation_annotations_preprocessing(
            internal_segmentation=self.internal_segmentation
        )


class MaskAnnotationCreationTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        # annotations_dict = extract_annotations_from_sff_segmentation(
        #     internal_segmentation=self.internal_segmentation
        # )
        mask_segmentation_annotations_preprocessing(
            internal_segmentation=self.internal_segmentation
        )


class NIIMetadataCollectionTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        volume = self.internal_volume
        metadata_dict = nii_volume_metadata_preprocessing(internal_volume=volume)


class MAPMetadataCollectionTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        volume = self.internal_volume
        metadata_dict = map_volume_metadata_preprocessing(v=volume)


class OMEZARRAnnotationsCollectionTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        annotations_dict = omezarr_volume_annotations_preprocessing(
            v=self.internal_volume
        )


class OMEZARRMetadataCollectionTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        metadata_dict = omezarr_volume_metadata_preprocessing(v=self.internal_volume)


class OMEZARRImageProcessTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        omezarr_volume_preprocessing(self.internal_volume)


class OMEZARRLabelsProcessTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        omezarr_segmentations_preprocessing(
            s=self.internal_segmentation
        )


class SFFMetadataCollectionTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        metadata_dict = sff_segmentation_metadata_preprocessing(
            s=self.internal_segmentation
        )


class MaskMetadataCollectionTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        # metadata_dict = extract_metadata_from_sff_segmentation(
        #     internal_segmentation=self.internal_segmentation
        # )
        metadata_dict = mask_segmentation_metadata_preprocessing(
            s=self.internal_segmentation
        )


class GeometricSegmentationMetadataCollectionTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        metadata_dict = geometric_segmentation_metadata_preprocessing(
            s=self.internal_segmentation
        )


class NIISegmentationMetadataCollectionTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        metadata_dict = nii_segmentation_metadata_preprocessing(
            internal_segmentation=self.internal_segmentation
        )


class ProcessVolumeTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        process_volume(self.internal_volume)


class ProcessVolumeMetadataTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        process_volume_metadata(self.internal_volume)


class ProcessVolumeAnnotationsTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        process_volume_annotations(self.internal_volume)


class ProcessSegmentationTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        process_segmentation(self.internal_segmentation)


class ProcessSegmentationMetadataTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        process_segmentation_metadata(self.internal_segmentation)


class ProcessSegmentationAnnotationsTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        process_segmentation_annotations(self.internal_segmentation)


class MAPProcessVolumeTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        volume = self.internal_volume

        map_volume_preprocessing(volume)
        # in processing part do
        volume_downsampling(volume)


class NIIProcessVolumeTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        volume = self.internal_volume

        nii_volume_preprocessing(volume)
        # in processing part do
        volume_downsampling(volume)


class OMETIFFImageProcessingTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        volume = self.internal_volume
        ometiff_volume_preprocessing(v=volume)
        volume_downsampling(internal_volume=volume)


class OMETIFFSegmentationProcessingTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        segmentation = self.internal_segmentation
        ometiff_segmentation_processing(s=segmentation)
        segmentation_downsampling(segmentation)


class OMETIFFImageMetadataExtractionTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        volume = self.internal_volume
        ometiff_volume_metadata_preprocessing(internal_volume=volume)


class OMETIFFSegmentationMetadataExtractionTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        internal_segmentation = self.internal_segmentation
        ometiff_segmentation_metadata_preprocessing(
            internal_segmentation=internal_segmentation
        )


class OMETIFFImageAnnotationsExtractionTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        volume = self.internal_volume
        ometiff_volume_annotations_preprocessing(internal_volume=volume)


class OMETIFFSegmentationAnnotationsExtractionTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        internal_segmentation = self.internal_segmentation
        ometiff_segmentation_annotations_preprocessing(
            internal_segmentation=internal_segmentation
        )


class TIFFImageStackDirProcessingTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        volume = self.internal_volume
        tiff_image_stack_dir_processing(internal_volume=volume)
        volume_downsampling(internal_volume=volume)

class TIFFSegmentationStackDirProcessingTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        internal_segmentation = self.internal_segmentation
        tiff_segmentation_stack_dir_processing(internal_segmentation)
        segmentation_downsampling(internal_segmentation)

class TIFFImageStackDirMetadataExtractionTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        volume = self.internal_volume
        extract_tiff_image_stack_dir_metadata(internal_volume=volume)

class TIFFSegmentationStackDirMetadataExtractionTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        extract_tiff_segmentation_stack_dir_metadata(self.internal_segmentation)

class TIFFSegmentationStackDirAnnotationCreationTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        mask_segmentation_annotations_preprocessing(internal_segmentation=self.internal_segmentation)

class ProcessExtraDataTask(TaskBase):
    def __init__(self, path: Path, intermediate_zarr_structure_path: Path):
        self.path = path
        self.intermediate_zarr_structure = intermediate_zarr_structure_path

    def execute(self) -> None:
        process_extra_data(self.path, self.intermediate_zarr_structure)


class AllencellMetadataCSVProcessingTask(TaskBase):
    def __init__(
        self, path: Path, cell_id: int, intermediate_zarr_structure_path: Path
    ):
        self.path = path
        self.cell_id = cell_id
        self.intermediate_zarr_structure = intermediate_zarr_structure_path

    def execute(self) -> None:
        process_allencell_metadata_csv(
            self.path, self.cell_id, self.intermediate_zarr_structure
        )


class NIIProcessSegmentationTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        segmentation = self.internal_segmentation

        nii_segmentation_preprocessing(internal_segmentation=segmentation)

        nii_segmentation_downsampling(internal_segmentation=segmentation)


class SFFProcessSegmentationTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        segmentation = self.internal_segmentation

        sff_segmentation_preprocessing(segmentation)

        segmentation_downsampling(segmentation)


class MaskProcessSegmentationTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        segmentation = self.internal_segmentation

        mask_segmentation_preprocessing(s=segmentation)
        segmentation_downsampling(segmentation)


class ProcessGeometricSegmentationTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        segmentation = self.internal_segmentation

        geometric_segmentation_preprocessing(s=segmentation)


class GeometricSegmentationAnnotationsCollectionTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        segmentation = self.internal_segmentation

        geometric_segmentation_annotations_preprocessing(s=segmentation)


class Preprocessor:
    def __init__(self, preprocessor_input: PreprocessorInput):
        if not preprocessor_input:
            raise ArgumentError("No input parameters are provided")
        self.preprocessor_input = preprocessor_input
        self.intermediate_zarr_structure = None
        self.internal_volume = None
        self.internal_segmentation = None

    def store_internal_volume(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def get_internal_volume(self):
        return self.internal_volume

    def store_internal_segmentation(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def get_internal_segmentation(self):
        return self.internal_segmentation

    # should be more complex than for loop
    # 1. check if there is mask
    # if yes - find all masks input
    # 2. check if there are geometric segmentations
    # if yes - find all geometric segmentation
    # 0. find extra data if any, and if yes, processs that first
    def _process_inputs(self, inputs: list[InputT]) -> list[TaskBase]:
        tasks = []

        # inputs = Pre/
        # if any(isinstance(i, MaskInput) for i in inputs):
        #     masks_inputs = list(filter(lambda m: isinstance(m, MaskInput), inputs))
        #     print(f'Mask inputs: {masks_inputs}')

        # if any(isinstance(i, GeometricSegmentationInput) for i in inputs):
        #     pass

        for i in inputs:
            if isinstance(i, ExtraDataInput):
                tasks.append(
                    ProcessExtraDataTask(
                        path=i.path,
                        intermediate_zarr_structure_path=self.intermediate_zarr_structure,
                    )
                )

            # rather use all without masks
            if isinstance(i, VOLUME_INPUT_TYPES):
                self.store_internal_volume(
                    internal_volume=InternalVolume(
                        path=self.intermediate_zarr_structure,
                        input_path=i.path,
                        params_for_storing=self.preprocessor_input.storing_params,
                        volume_force_dtype=self.preprocessor_input.volume.force_volume_dtype,
                        quantize_dtype_str=self.preprocessor_input.volume.quantize_dtype_str,
                        downsampling_parameters=self.preprocessor_input.downsampling,
                        entry_data=self.preprocessor_input.entry_data,
                        quantize_downsampling_levels=self.preprocessor_input.volume.quantize_downsampling_levels,
                        input_kind=i.kind,
                    )
                )
                volume = self.get_internal_volume()
                tasks.append(ProcessVolumeTask(volume))

                tasks.append(ProcessVolumeMetadataTask(volume))

                tasks.append(ProcessVolumeAnnotationsTask(volume))

            # pre-analyze inputs list in analyze inputs
            # remove all masks instances
            # insert a single one with input path as list
            # then do this below
            if isinstance(i, SEGMENTATION_INPUT_TYPES):
                self.store_internal_segmentation(
                    internal_segmentation=InternalSegmentation(
                        path=self.intermediate_zarr_structure,
                        input_path=i.path,
                        params_for_storing=self.preprocessor_input.storing_params,
                        downsampling_parameters=self.preprocessor_input.downsampling,
                        entry_data=self.preprocessor_input.entry_data,
                        input_kind=i.kind,
                    )
                )

                segmentation = self.get_internal_segmentation()
                tasks.append(ProcessSegmentationTask(segmentation))
                tasks.append(ProcessSegmentationMetadataTask(segmentation))
                tasks.append(ProcessSegmentationAnnotationsTask(segmentation))

            # elif isinstance(i, MAPInput):
            #     self.store_internal_volume(
            #         internal_volume=InternalVolume(
            #             intermediate_zarr_structure_path=self.intermediate_zarr_structure,
            #             volume_input_path=i.input_path,
            #             params_for_storing=self.preprocessor_input.storing_params,
            #             volume_force_dtype=self.preprocessor_input.volume.force_volume_dtype,
            #             quantize_dtype_str=self.preprocessor_input.volume.quantize_dtype_str,
            #             downsampling_parameters=self.preprocessor_input.downsampling,
            #             entry_data=self.preprocessor_input.entry_data,
            #             quantize_downsampling_levels=self.preprocessor_input.volume.quantize_downsampling_levels,
            #         )
            #     )
            #     tasks.append(
            #         MAPProcessVolumeTask(internal_volume=self.get_internal_volume())
            #     )
            #     tasks.append(
            #         MAPMetadataCollectionTask(
            #             internal_volume=self.get_internal_volume()
            #         )
            #     )
            # elif isinstance(i, SFFInput):
            #     self.store_internal_segmentation(
            #         internal_segmentation=InternalSegmentation(
            #             intermediate_zarr_structure_path=self.intermediate_zarr_structure,
            #             segmentation_input_path=i.input_path,
            #             params_for_storing=self.preprocessor_input.storing_params,
            #             downsampling_parameters=self.preprocessor_input.downsampling,
            #             entry_data=self.preprocessor_input.entry_data,
            #         )
            #     )
            #     tasks.append(
            #         SFFProcessSegmentationTask(
            #             internal_segmentation=self.get_internal_segmentation()
            #         )
            #     )
            #     tasks.append(
            #         SFFMetadataCollectionTask(
            #             internal_segmentation=self.get_internal_segmentation()
            #         )
            #     )
            #     tasks.append(
            #         SFFAnnotationCollectionTask(
            #             internal_segmentation=self.get_internal_segmentation()
            #         )
            #     )

            # elif isinstance(i, MaskInput):
            #     mask_segmentation_inputs.append(i)

            # elif isinstance(i, OMEZARRInput):
            #     self.store_internal_volume(
            #         internal_volume=InternalVolume(
            #             intermediate_zarr_structure_path=self.intermediate_zarr_structure,
            #             volume_input_path=i.input_path,
            #             params_for_storing=self.preprocessor_input.storing_params,
            #             volume_force_dtype=self.preprocessor_input.volume.force_volume_dtype,
            #             quantize_dtype_str=self.preprocessor_input.volume.quantize_dtype_str,
            #             downsampling_parameters=self.preprocessor_input.downsampling,
            #             entry_data=self.preprocessor_input.entry_data,
            #             quantize_downsampling_levels=self.preprocessor_input.volume.quantize_downsampling_levels,
            #         )
            #     )
            #     tasks.append(OMEZARRImageProcessTask(self.get_internal_volume()))
            #     if check_if_omezarr_has_labels(
            #         internal_volume=self.get_internal_volume()
            #     ):
            #         self.store_internal_segmentation(
            #             internal_segmentation=InternalSegmentation(
            #                 intermediate_zarr_structure_path=self.intermediate_zarr_structure,
            #                 segmentation_input_path=i.input_path,
            #                 params_for_storing=self.preprocessor_input.storing_params,
            #                 downsampling_parameters=self.preprocessor_input.downsampling,
            #                 entry_data=self.preprocessor_input.entry_data,
            #             )
            #         )
            #         tasks.append(
            #             OMEZARRLabelsProcessTask(self.get_internal_segmentation())
            #         )

            #     tasks.append(
            #         OMEZARRMetadataCollectionTask(
            #             internal_volume=self.get_internal_volume()
            #         )
            #     )
            #     tasks.append(
            #         OMEZARRAnnotationsCollectionTask(self.get_internal_volume())
            #     )

            # elif isinstance(i, GeometricSegmentationInput):
            #     self.store_internal_segmentation(
            #         internal_segmentation=InternalSegmentation(
            #             intermediate_zarr_structure_path=self.intermediate_zarr_structure,
            #             segmentation_input_path=i.input_path,
            #             params_for_storing=self.preprocessor_input.storing_params,
            #             downsampling_parameters=self.preprocessor_input.downsampling,
            #             entry_data=self.preprocessor_input.entry_data,
            #         )
            #     )
            #     tasks.append(
            #         ProcessGeometricSegmentationTask(self.get_internal_segmentation())
            #     )
            # elif isinstance(i, OMETIFFImageInput):
            #     self.store_internal_volume(
            #         internal_volume=InternalVolume(
            #             intermediate_zarr_structure_path=self.intermediate_zarr_structure,
            #             volume_input_path=i.input_path,
            #             params_for_storing=self.preprocessor_input.storing_params,
            #             volume_force_dtype=self.preprocessor_input.volume.force_volume_dtype,
            #             quantize_dtype_str=self.preprocessor_input.volume.quantize_dtype_str,
            #             downsampling_parameters=self.preprocessor_input.downsampling,
            #             entry_data=self.preprocessor_input.entry_data,
            #             quantize_downsampling_levels=self.preprocessor_input.volume.quantize_downsampling_levels,
            #         )
            #     )
            #     tasks.append(
            #         OMETIFFImageProcessingTask(
            #             internal_volume=self.get_internal_volume()
            #         )
            #     )
            #     tasks.append(
            #         OMETIFFImageMetadataExtractionTask(
            #             internal_volume=self.get_internal_volume()
            #         )
            #     )
            #     # TODO: remove - after processing segmentation
            #     tasks.append(
            #         OMETIFFImageAnnotationsExtractionTask(
            #             internal_volume=self.get_internal_volume()
            #         )
            #     )
            # elif isinstance(i, OMETIFFSegmentationInput):
            #     self.store_internal_segmentation(
            #         internal_segmentation=InternalSegmentation(
            #             intermediate_zarr_structure_path=self.intermediate_zarr_structure,
            #             segmentation_input_path=i.input_path,
            #             params_for_storing=self.preprocessor_input.storing_params,
            #             downsampling_parameters=self.preprocessor_input.downsampling,
            #             entry_data=self.preprocessor_input.entry_data,
            #         )
            #     )
            #     tasks.append(
            #         OMETIFFSegmentationProcessingTask(self.get_internal_segmentation())
            #     )
            #     tasks.append(
            #         OMETIFFSegmentationMetadataExtractionTask(
            #             internal_segmentation=self.get_internal_segmentation()
            #         )
            #     )
            #     tasks.append(
            #         OMETIFFSegmentationAnnotationsExtractionTask(
            #             internal_segmentation=self.get_internal_segmentation()
            #         )
            #     )
            # elif isinstance(i, NIIVolumeInput):
            #     self.store_internal_volume(
            #         internal_volume=InternalVolume(
            #             intermediate_zarr_structure_path=self.intermediate_zarr_structure,
            #             volume_input_path=i.input_path,
            #             params_for_storing=self.preprocessor_input.storing_params,
            #             volume_force_dtype=self.preprocessor_input.volume.force_volume_dtype,
            #             quantize_dtype_str=self.preprocessor_input.volume.quantize_dtype_str,
            #             downsampling_parameters=self.preprocessor_input.downsampling,
            #             entry_data=self.preprocessor_input.entry_data,
            #             quantize_downsampling_levels=self.preprocessor_input.volume.quantize_downsampling_levels,
            #         )
            #     )
            #     tasks.append(
            #         NIIProcessVolumeTask(internal_volume=self.get_internal_volume())
            #     )
            #     tasks.append(
            #         NIIMetadataCollectionTask(
            #             internal_volume=self.get_internal_volume()
            #         )
            #     )

            # elif isinstance(i, NIISegmentationInput):
            #     nii_segmentation_inputs.append(i)
            # elif isinstance(i, CustomAnnotationsInput):
            #     tasks.append(
            #         CustomAnnotationsCollectionTask(
            #             input_path=i.input_path,
            #             intermediate_zarr_structure_path=self.intermediate_zarr_structure,
            #         )
            #     )

        if (
            self.get_internal_volume()
            and self.preprocessor_input.volume.quantize_dtype_str
        ):
            tasks.append(
                QuantizeInternalVolumeTask(internal_volume=self.get_internal_volume())
            )

        # if nii_segmentation_inputs:
        #     nii_segmentation_input_paths = [
        #         i.input_path for i in nii_segmentation_inputs
        #     ]
        #     self.store_internal_segmentation(
        #         internal_segmentation=InternalSegmentation(
        #             intermediate_zarr_structure_path=self.intermediate_zarr_structure,
        #             segmentation_input_path=nii_segmentation_input_paths,
        #             params_for_storing=self.preprocessor_input.storing_params,
        #             downsampling_parameters=self.preprocessor_input.downsampling,
        #             entry_data=self.preprocessor_input.entry_data,
        #         )
        #     )
        #     tasks.append(
        #         NIIProcessSegmentationTask(
        #             internal_segmentation=self.get_internal_segmentation()
        #         )
        #     )
        #     tasks.append(
        #         NIISegmentationMetadataCollectionTask(
        #             internal_segmentation=self.get_internal_segmentation()
        #         )
        #     )

        # masks
        # if mask_segmentation_inputs:
        #     mask_segmentation_input_paths = [
        #         i.input_path for i in mask_segmentation_inputs
        #     ]
        #     self.store_internal_segmentation(
        #         internal_segmentation=InternalSegmentation(
        #             intermediate_zarr_structure_path=self.intermediate_zarr_structure,
        #             segmentation_input_path=mask_segmentation_input_paths,
        #             params_for_storing=self.preprocessor_input.storing_params,
        #             downsampling_parameters=self.preprocessor_input.downsampling,
        #             entry_data=self.preprocessor_input.entry_data,
        #         )
        #     )
        #     tasks.append(
        #         MaskProcessSegmentationTask(
        #             internal_segmentation=self.get_internal_segmentation()
        #         )
        #     )
        #     tasks.append(
        #         MaskMetadataCollectionTask(
        #             internal_segmentation=self.get_internal_segmentation()
        #         )
        #     )

        #     tasks.append(
        #         MaskAnnotationCreationTask(
        #             internal_segmentation=self.get_internal_segmentation()
        #         )
        #     )

        # if any(isinstance(i, GeometricSegmentationInput) for i in inputs):
        #     # tasks.append(SaveGeometricSegmentationSets(self.intermediate_zarr_structure))
        #     tasks.append(
        #         GeometricSegmentationAnnotationsCollectionTask(
        #             self.get_internal_segmentation()
        #         )
        #     )
        #     tasks.append(
        #         GeometricSegmentationMetadataCollectionTask(
        #             self.get_internal_segmentation()
        #         )
        #     )

        # tasks.append(SaveMetadataTask(self.intermediate_zarr_structure))
        # tasks.append(SaveAnnotationsTask(self.intermediate_zarr_structure))

        return tasks

    def _execute_tasks(self, tasks: list[TaskBase]):
        for task in tasks:
            task.execute()

    def __check_if_inputs_exists(self, raw_inputs_list: list[RawInput]):
        for input_item in raw_inputs_list:
            p = input_item.path
            assert p.exists(), f"Input file {p} does not exist"

    def _analyse_preprocessor_input(self) -> list[InputT]:
        raw_inputs_list = self.preprocessor_input.inputs.files
        # analyzed_inputs: list[InputT] = []

        self.__check_if_inputs_exists(raw_inputs_list)

        analyzed: list[InputT] = []

        extra_data = list(
            filter(lambda i: i.kind == InputKind.extra_data, raw_inputs_list)
        )
        assert len(extra_data) <= 1, "There must be no more than one extra data input"
        if len(extra_data) == 1:
            analyzed.append(extra_data[0])

        if any(i.kind == InputKind.mask for i in raw_inputs_list):
            all_mask_input_pathes = [
                i.path for i in raw_inputs_list if i.kind == InputKind.mask
            ]
            joint_mask_input = MaskInput(
                path=all_mask_input_pathes, kind=InputKind.mask
            )
            analyzed.append(joint_mask_input)

        if any(i.kind == InputKind.geometric_segmentation for i in raw_inputs_list):
            all_gs_pathes = [
                i.path
                for i in raw_inputs_list
                if i.kind == InputKind.geometric_segmentation
            ]
            joint_geometric_segmentation_input = GeometricSegmentationInput(
                all_gs_pathes, InputKind.geometric_segmentation
            )
            analyzed.append(joint_geometric_segmentation_input)

        # TODO: three maps etc.?

        for i in raw_inputs_list:
            k = i.kind
            p = i.path
            if k == InputKind.extra_data:
                analyzed.append(ExtraDataInput(path=p, kind=k))
            elif k == InputKind.map:
                analyzed.append(MAPInput(path=p, kind=k))
            elif k == InputKind.sff:
                analyzed.append(SFFInput(path=p, kind=k))
            elif k == InputKind.omezarr:
                analyzed.append(OMEZARRInput(path=p, kind=k))
            elif k == InputKind.mask:
                analyzed.append(MaskInput(path=p, kind=k))
            elif k == InputKind.geometric_segmentation:
                analyzed.append(GeometricSegmentationInput(path=p, kind=k))
            elif k == InputKind.custom_annotations:
                analyzed.append(CustomAnnotationsInput(path=p, kind=k))
            elif k == InputKind.application_specific_segmentation:
                sff_path = convert_app_specific_segm_to_sff(i.path)
                analyzed.append(SFFInput(path=sff_path, kind=InputKind.sff))
                # TODO: remove app specific segm file?
            elif k == InputKind.ometiff_image:
                analyzed.append(OMETIFFImageInput(path=p, kind=k))
            elif k == InputKind.ometiff_segmentation:
                analyzed.append(OMETIFFSegmentationInput(path=p, kind=k))
            elif k == InputKind.tiff_image_stack_dir:
                analyzed.append(TIFFImageStackDirInput(path=p, kind=k))
            elif k == InputKind.tiff_segmentation_stack_dir:
                analyzed.append(TIFFSegmentationStackDirInput(path=p, kind=k))
            else:
                raise Exception(f"Input kind is not recognized. Input item: {i}")

        print(f"pre_analyzed_inputs_list: {analyzed}")
        return analyzed

    async def entry_exists(self):
        new_db_path = Path(self.preprocessor_input.db_path)
        if new_db_path.is_dir() == False:
            new_db_path.mkdir(parents=True)

        db = FileSystemVolumeServerDB(new_db_path, store_type="zip")

        exists = await db.contains(
            namespace=self.preprocessor_input.entry_data.source_db,
            key=self.preprocessor_input.entry_data.entry_id,
        )

        return exists

    async def initialization(self, mode: PreprocessorMode, extra_metadata: ExtraMetadata):
        self.intermediate_zarr_structure = (
            self.preprocessor_input.working_folder
            / self.preprocessor_input.entry_data.entry_id
        )
        try:
            # delete previous intermediate zarr structure
            shutil.rmtree(self.intermediate_zarr_structure, ignore_errors=True)
            assert (
                self.intermediate_zarr_structure.exists() == False
            ), f"intermediate_zarr_structure: {self.intermediate_zarr_structure} already exists"
            store: zarr.storage.DirectoryStore = zarr.DirectoryStore(
                str(self.intermediate_zarr_structure)
            )
            root = zarr.group(store=store)

            # first initialize metadata and annotations dicts as empty
            # or as dicts read from db if mode is "extend"
            if mode == PreprocessorMode.extend:
                new_db_path = Path(self.preprocessor_input.db_path)
                db = FileSystemVolumeServerDB(new_db_path, store_type="zip")
                volume_metadata = await db.read_metadata(
                    self.preprocessor_input.entry_data.source_db,
                    self.preprocessor_input.entry_data.entry_id,
                )
                root.attrs["metadata_dict"] = volume_metadata.dict()
                root.attrs["annotations_dict"] = await db.read_annotations(
                    self.preprocessor_input.entry_data.source_db,
                    self.preprocessor_input.entry_data.entry_id,
                )

            elif mode == PreprocessorMode.add:
                init_metadata_model = INIT_METADATA_MODEL.copy()
                init_annotations_model = INIT_ANNOTATIONS_MODEL.copy()
                if extra_metadata is not None:
                    init_metadata_model.extra_metadata = extra_metadata
                    
                root.attrs["metadata_dict"] = init_metadata_model.dict()

                root.attrs["annotations_dict"] = init_annotations_model.dict()
            else:
                raise Exception("Preprocessor mode is not supported")
            # init GeometricSegmentationData in zattrs
            root.attrs[GEOMETRIC_SEGMENTATIONS_ZATTRS] = []
            root.attrs[RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS] = {}

        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e

        # self._analyse_preprocessor_input()

    def preprocessing(self):
        inputs = self._analyse_preprocessor_input()
        tasks = self._process_inputs(inputs)
        self._execute_tasks(tasks)
        return

    def store_to_db(self, mode: PreprocessorMode):
        new_db_path = Path(self.preprocessor_input.db_path)
        if new_db_path.is_dir() == False:
            new_db_path.mkdir()

        db = FileSystemVolumeServerDB(new_db_path, store_type="zip")

        # call it once and get context
        # get segmentation_ids from metadata
        # using its method
        root = open_zarr(self.intermediate_zarr_structure)

        segmentation_lattice_ids = []
        segmentation_mesh_ids = []
        geometric_segmentation_ids = []

        if LATTICE_SEGMENTATION_DATA_GROUPNAME in root:
            segmentation_lattice_ids = list(
                root[LATTICE_SEGMENTATION_DATA_GROUPNAME].group_keys()
            )
        if MESH_SEGMENTATION_DATA_GROUPNAME in root:
            segmentation_mesh_ids = list(
                root[MESH_SEGMENTATION_DATA_GROUPNAME].group_keys()
            )
        if GEOMETRIC_SEGMENTATIONS_ZATTRS in root.attrs:
            geometric_segm_attrs: list[GeometricSegmentationData] = root.attrs[
                GEOMETRIC_SEGMENTATIONS_ZATTRS
            ]
            geometric_segmentation_ids = [
                g["segmentation_id"] for g in geometric_segm_attrs
            ]

        with db.edit_data(
            namespace=self.preprocessor_input.entry_data.source_db,
            key=self.preprocessor_input.entry_data.entry_id,
            working_folder=self.preprocessor_input.working_folder,
        ) as db_edit_context:
            db_edit_context: VolumeAndSegmentationContext
            # adding volume
            if VOLUME_DATA_GROUPNAME in root:
                db_edit_context.add_volume()
            # adding segmentations
            for id in segmentation_lattice_ids:
                db_edit_context.add_segmentation(id=id, kind="lattice")
            for id in segmentation_mesh_ids:
                db_edit_context.add_segmentation(id=id, kind="mesh")
            for id in geometric_segmentation_ids:
                db_edit_context.add_segmentation(id=id, kind="geometric_segmentation")
        if mode == PreprocessorMode.add:
            print(
                f"Entry {self.preprocessor_input.entry_data.entry_id} stored to the database"
            )
        else:
            print(
                f"Entry {self.preprocessor_input.entry_data.entry_id} in the database was expanded"
            )


async def main_preprocessor(
    a: PreprocessorArguments,
    # mode: PreprocessorMode,
    # quantize_dtype_str: typing.Optional[QuantizationDtype],
    # quantize_downsampling_levels: typing.Optional[str],
    # force_volume_dtype: typing.Optional[str],
    # max_size_per_downsampling_lvl_mb: typing.Optional[float],
    # min_downsampling_level: typing.Optional[int],
    # max_downsampling_level: typing.Optional[int],
    # remove_original_resolution: bool,
    # entry_id: str,
    # source_db: str,
    # source_db_id: str,
    # source_db_name: str,
    # working_folder: str,
    # db_path: str,
    # input_paths: list[str],
    # input_kinds: list[InputKind],
    # min_size_per_downsampling_lvl_mb: typing.Optional[float] = 5.0,
):
    # for k, v in arguments.items():
    #     setattr(args, k, v)
    
    extra_metadata = ExtraMetadata()
    if a.pre_downsampling_factor:
        extra_metadata.pre_downsampling_factor = int(a.pre_downsampling_factor)
        # should not exclude extra data a
        input_paths = pre_downsample_data(a.inputs, extra_metadata.pre_downsampling_factor, a.working_folder)
    
    preprocessor_input = PreprocessorInput(
        inputs=Inputs(files=[]),
        volume=VolumeParams(
            quantize_dtype_str=a.quantize_dtype_str,
            quantize_downsampling_levels=a.quantize_downsampling_levels,
            force_volume_dtype=a.force_volume_dtype,
        ),
        downsampling=DownsamplingParams(
            min_size_per_downsampling_lvl_mb=a.min_size_per_downsampling_lvl_mb,
            max_size_per_downsampling_lvl_mb=a.max_size_per_downsampling_lvl_mb,
            min_downsampling_level=a.min_downsampling_level,
            max_downsampling_level=a.max_downsampling_level,
            remove_original_resolution=a.remove_original_resolution,
        ),
        entry_data=EntryData(
            entry_id=a.entry_id,
            source_db=a.source_db,
            source_db_id=a.source_db_id,
            source_db_name=a.source_db_name,
        ),
        working_folder=Path(a.working_folder),
        storing_params=StoringParams(),
        db_path=Path(a.db_path),
    )

    inputs: list[RawInput] = a.inputs
    for idx, i in enumerate(inputs):
        inputs[idx] = RawInput(path=Path(i.path), kind=i.kind)

    # for input_path, input_kind in zip(args.input_paths, args.input_kinds):
    preprocessor_input.inputs.files = inputs

    preprocessor = Preprocessor(preprocessor_input)
    if a.mode == PreprocessorMode.add:
        if await preprocessor.entry_exists():
            raise Exception(
                f"Entry {preprocessor_input.entry_data.entry_id} from {preprocessor_input.entry_data.source_db} source already exists in database {preprocessor_input.db_path}"
            )
    else:
        if not await preprocessor.entry_exists():
            raise Exception(
                f"Entry {preprocessor_input.entry_data.entry_id} from {preprocessor_input.entry_data.source_db} source does not exist in database {preprocessor_input.db_path}"
            )
        assert (
            a.mode == PreprocessorMode.extend
        ), "Preprocessor mode is not supported"

    await preprocessor.initialization(mode=a.mode, extra_metadata=extra_metadata)
    preprocessor.preprocessing()
    preprocessor.store_to_db(mode=a.mode)


app = typer.Typer()


# NOTE: works as adding, i.e. if entry already has volume/segmentation
# it will not add anything, throwing error instead (group exists in destination)
@app.command("preprocess")
def main(
    arguments_json: str = typer.Option(default=...),
    # mode: PreprocessorMode = PreprocessorMode.add.value,
    # quantize_dtype_str: Annotated[
    #     typing.Optional[QuantizationDtype], typer.Option(None)
    # ] = None,
    # quantize_downsampling_levels: Annotated[
    #     typing.Optional[str], typer.Option(None, help="Space-separated list of numbers")
    # ] = None,
    # force_volume_dtype: Annotated[typing.Optional[str], typer.Option(None)] = None,
    # max_size_per_downsampling_lvl_mb: Annotated[
    #     typing.Optional[float], typer.Option(None)
    # ] = None,
    # min_size_per_downsampling_lvl_mb: Annotated[
    #     typing.Optional[float], typer.Option(None)
    # ] = 5.0,
    # min_downsampling_level: Annotated[typing.Optional[int], typer.Option(None)] = None,
    # max_downsampling_level: Annotated[typing.Optional[int], typer.Option(None)] = None,
    # remove_original_resolution: Annotated[
    #     typing.Optional[bool], typer.Option(None)
    # ] = False,
    # entry_id: str = typer.Option(default=...),
    # source_db: str = typer.Option(default=...),
    # source_db_id: str = typer.Option(default=...),
    # source_db_name: str = typer.Option(default=...),
    # working_folder: str = typer.Option(default=...),
    # db_path: str = typer.Option(default=...),
    # input_path: list[str] = typer.Option(default=...),
    # input_kind: list[InputKind] = typer.Option(default=...),
    # # add_segmentation_to_entry: bool = typer.Option(default=False),
    # # add_custom_annotations: bool = typer.Option(default=False),
):
    json_path = Path(arguments_json)
    arguments: PreprocessorArguments = read_json(json_path)
    # TODO: unpack to variables
    asyncio.run(
        main_preprocessor(
            a=arguments
            # mode=mode,
            # entry_id=entry_id,
            # source_db=source_db,
            # source_db_id=source_db_id,
            # source_db_name=source_db_name,
            # working_folder=working_folder,
            # db_path=db_path,
            # input_paths=input_path,
            # input_kinds=input_kind,
            # quantize_dtype_str=quantize_dtype_str,
            # quantize_downsampling_levels=quantize_downsampling_levels,
            # force_volume_dtype=force_volume_dtype,
            # max_size_per_downsampling_lvl_mb=max_size_per_downsampling_lvl_mb,
            # min_size_per_downsampling_lvl_mb=min_size_per_downsampling_lvl_mb,
            # min_downsampling_level=min_downsampling_level,
            # max_downsampling_level=max_downsampling_level,
            # remove_original_resolution=remove_original_resolution,
            # # add_segmentation_to_entry=add_segmentation_to_entry,
            # # add_custom_annotations=add_custom_annotations
        )
    )


@app.command("delete")
def delete_entry(
    entry_id: str = typer.Option(default=...),
    source_db: str = typer.Option(default=...),
    db_path: str = typer.Option(default=...),
):
    print(f"Deleting db entry: {entry_id} {source_db}")
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    db = FileSystemVolumeServerDB(new_db_path, store_type="zip")
    asyncio.run(db.delete(namespace=source_db, key=entry_id))


@app.command("remove-volume")
def remove_volume(
    entry_id: str = typer.Option(default=...),
    source_db: str = typer.Option(default=...),
    db_path: str = typer.Option(default=...),
    working_folder: str = typer.Option(default=...),
):
    print(f"Deleting volumes for entry: {entry_id} {source_db}")
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    db = FileSystemVolumeServerDB(new_db_path, store_type="zip")

    with db.edit_data(
        namespace=source_db, key=entry_id, working_folder=Path(working_folder)
    ) as db_edit_context:
        db_edit_context: VolumeAndSegmentationContext
        db_edit_context.remove_volume()


@app.command("remove-segmentation")
def remove_segmentation(
    entry_id: str = typer.Option(default=...),
    source_db: str = typer.Option(default=...),
    id: str = typer.Option(default=...),
    kind: str = typer.Option(default=...),
    db_path: str = typer.Option(default=...),
    working_folder: str = typer.Option(default=...),
):
    print(f"Deleting segmentation for entry: {entry_id} {source_db}")
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    db = FileSystemVolumeServerDB(new_db_path, store_type="zip")

    with db.edit_data(
        namespace=source_db, key=entry_id, working_folder=Path(working_folder)
    ) as db_edit_context:
        db_edit_context: VolumeAndSegmentationContext
        db_edit_context.remove_segmentation(id=id, kind=kind)


@app.command("remove-segment-annotations")
def remove_segment_annotations(
    entry_id: str = typer.Option(default=...),
    source_db: str = typer.Option(default=...),
    id: list[str] = typer.Option(default=...),
    db_path: str = typer.Option(default=...),
):
    print(f"Deleting annotation for entry: {entry_id} {source_db}")
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    db = FileSystemVolumeServerDB(new_db_path, store_type="zip")

    with db.edit_annotations(
        namespace=source_db, key=entry_id
    ) as db_edit_annotations_context:
        db_edit_annotations_context: AnnnotationsEditContext
        asyncio.run(db_edit_annotations_context.remove_segment_annotations(ids=id))


@app.command("remove-descriptions")
def remove_descriptions(
    entry_id: str = typer.Option(default=...),
    source_db: str = typer.Option(default=...),
    id: list[str] = typer.Option(default=...),
    db_path: str = typer.Option(default=...),
):
    print(f"Deleting descriptions for entry: {entry_id} {source_db}")
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    db = FileSystemVolumeServerDB(new_db_path, store_type="zip")

    with db.edit_annotations(
        namespace=source_db, key=entry_id
    ) as db_edit_annotations_context:
        db_edit_annotations_context: AnnnotationsEditContext
        asyncio.run(db_edit_annotations_context.remove_descriptions(ids=id))


@app.command("edit-segment-annotations")
def edit_segment_annotations(
    entry_id: str = typer.Option(default=...),
    source_db: str = typer.Option(default=...),
    # id: list[str] = typer.Option(default=...),
    data_json_path: str = typer.Option(default=...),
    db_path: str = typer.Option(default=...),
):
    # print(f"Deleting descriptions for entry: {entry_id} {source_db}")
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    db = FileSystemVolumeServerDB(new_db_path, store_type="zip")

    parsedSegmentAnnotations: list[SegmentAnnotationData] = read_json(
        Path(data_json_path)
    )

    with db.edit_annotations(
        namespace=source_db, key=entry_id
    ) as db_edit_annotations_context:
        db_edit_annotations_context: AnnnotationsEditContext
        asyncio.run(
            db_edit_annotations_context.add_or_modify_segment_annotations(
                parsedSegmentAnnotations
            )
        )


@app.command("edit-descriptions")
def edit_descriptions(
    entry_id: str = typer.Option(default=...),
    source_db: str = typer.Option(default=...),
    # id: list[str] = typer.Option(default=...),
    data_json_path: str = typer.Option(default=...),
    db_path: str = typer.Option(default=...),
):
    # print(f"Deleting descriptions for entry: {entry_id} {source_db}")
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    db = FileSystemVolumeServerDB(new_db_path, store_type="zip")

    parsedDescriptionData: list[DescriptionData] = read_json(Path(data_json_path))

    with db.edit_annotations(
        namespace=source_db, key=entry_id
    ) as db_edit_annotations_context:
        db_edit_annotations_context: AnnnotationsEditContext
        asyncio.run(
            db_edit_annotations_context.add_or_modify_descriptions(
                parsedDescriptionData
            )
        )


if __name__ == "__main__":
    # solutions how to run it async - two last https://github.com/tiangolo/typer/issues/85
    # currently using last one
    # typer.run(main)

    # could try https://github.com/tiangolo/typer/issues/88#issuecomment-1732469681
    app()


# NOTE: for testing:
# python preprocessor/preprocessor/preprocess.py --input-path temp/v2_temp_static_entry_files_dir/idr/idr-6001247/6001247.zarr --input-kind omezarr
# python preprocessor/preprocessor/preprocess.py --input-path test-data/preprocessor/sample_volumes/emdb_sff/EMD-1832.map --input-kind map --input-path test-data/preprocessor/sample_segmentations/emdb_sff/emd_1832.hff --input-kind sff
