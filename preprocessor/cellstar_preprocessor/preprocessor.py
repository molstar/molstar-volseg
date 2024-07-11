import asyncio
import logging
import shutil
import typing
from argparse import ArgumentError
from pathlib import Path

from cellstar_preprocessor.commands.delete_entry import delete_entry
from cellstar_preprocessor.commands.edit_descriptions import edit_descriptions
from cellstar_preprocessor.commands.edit_segment_annotations import edit_segment_annotations
from cellstar_preprocessor.commands.remove_descriptions import remove_descriptions
from cellstar_preprocessor.commands.remove_segment_annotations import remove_segment_annotations
from cellstar_preprocessor.commands.remove_segmentation import remove_segmentation
from cellstar_preprocessor.commands.remove_volume import remove_volume
from cellstar_preprocessor.flows.volume.pre_downsample_data import pre_downsample_data
from cellstar_preprocessor.tools.wrl_to_stl.wrl_to_stl import wrl_to_stl
import typer
import zarr
from cellstar_db.file_system.db import FileSystemVolumeServerDB
from cellstar_db.file_system.volume_and_segmentation_context import (
    VolumeAndSegmentationContext,
)
from cellstar_db.models import (
    DownsamplingParams,
    EntryData,
    ExtraMetadata,
    GeometricSegmentationData,
    AssetKind,
    GeneralPreprocessorParameters,
    Inputs,
    PreprocessorInput,
    PreprocessorMode,
    RawInput,
    StoringParams,
    VolumeParams,
)
from cellstar_preprocessor.flows.common import process_extra_data, read_json
from cellstar_preprocessor.flows.constants import (
    ANNOTATIONS_DICT_NAME,
    GEOMETRIC_SEGMENTATIONS_ZATTRS,
    INIT_ANNOTATIONS_MODEL,
    INIT_METADATA_MODEL,
    LATTICE_SEGMENTATION_DATA_GROUPNAME,
    MESH_SEGMENTATION_DATA_GROUPNAME,
    METADATA_DICT_NAME,
    RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS,
    VOLUME_DATA_GROUPNAME,
)
from cellstar_preprocessor.flows.segmentation.custom_annotations_preprocessing import (
    custom_annotations_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.tiff_segmentation_stack_dir_metadata_preprocessing import (
    tiff_segmentation_stack_dir_metadata_preprocessing,
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
from cellstar_preprocessor.flows.segmentation.tiff_stack_dir_segmentation_preprocessing import (
    tiff_stack_dir_segmentation_preprocessing,
)
from cellstar_preprocessor.flows.volume.tiff_image_stack_dir_metadata_preprocessing import (
    tiff_image_stack_dir_metadata_preprocessing,
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
from cellstar_preprocessor.flows.volume.tiff_image_stack_dir_processing import (
    tiff_image_stack_dir_processing,
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
    kind: AssetKind


class TIFFImageStackDirInput(InputT):
    pass


class TIFFSegmentationStackDirInput(InputT):
    pass

class STLSegmentationInput(InputT):
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
    TIFFSegmentationStackDirInput,
    STLSegmentationInput
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
        ometiff_volume_metadata_preprocessing(v=volume)


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
        ometiff_volume_annotations_preprocessing(v=volume)


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
        tiff_image_stack_dir_processing(i=volume)
        volume_downsampling(internal_volume=volume)


class TIFFSegmentationStackDirProcessingTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        internal_segmentation = self.internal_segmentation
        tiff_stack_dir_segmentation_preprocessing(internal_segmentation)
        segmentation_downsampling(internal_segmentation)


class TIFFImageStackDirMetadataExtractionTask(TaskBase):
    def __init__(self, internal_volume: InternalVolume):
        self.internal_volume = internal_volume

    def execute(self) -> None:
        volume = self.internal_volume
        tiff_image_stack_dir_metadata_preprocessing(v=volume)


class TIFFSegmentationStackDirMetadataExtractionTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        tiff_segmentation_stack_dir_metadata_preprocessing(self.internal_segmentation)


class TIFFSegmentationStackDirAnnotationCreationTask(TaskBase):
    def __init__(self, internal_segmentation: InternalSegmentation):
        self.internal_segmentation = internal_segmentation

    def execute(self) -> None:
        mask_segmentation_annotations_preprocessing(
            s=self.internal_segmentation
        )


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
            filter(lambda i: i.kind == AssetKind.extra_data, raw_inputs_list)
        )
        assert len(extra_data) <= 1, "There must be no more than one extra data input"
        if len(extra_data) == 1:
            analyzed.append(extra_data[0])

        if any(i.kind == AssetKind.mask for i in raw_inputs_list):
            all_mask_input_pathes = [
                i.path for i in raw_inputs_list if i.kind == AssetKind.mask
            ]
            joint_mask_input = MaskInput(
                path=all_mask_input_pathes, kind=AssetKind.mask
            )
            analyzed.append(joint_mask_input)

        if any(i.kind == AssetKind.geometric_segmentation for i in raw_inputs_list):
            all_gs_pathes = [
                i.path
                for i in raw_inputs_list
                if i.kind == AssetKind.geometric_segmentation
            ]
            joint_geometric_segmentation_input = GeometricSegmentationInput(
                all_gs_pathes, AssetKind.geometric_segmentation
            )
            analyzed.append(joint_geometric_segmentation_input)

        # TODO: three maps etc.?

        for i in raw_inputs_list:
            k = i.kind
            p = i.path
            match k:
                case AssetKind.extra_data:
                    analyzed.append(ExtraDataInput(path=p, kind=k))
                case AssetKind.map:
                    analyzed.append(MAPInput(path=p, kind=k))
                case AssetKind.sff:
                    analyzed.append(SFFInput(path=p, kind=k))
                case AssetKind.omezarr:
                    analyzed.append(OMEZARRInput(path=p, kind=k))
                case AssetKind.mask:
                    analyzed.append(MaskInput(path=p, kind=k))
                case AssetKind.geometric_segmentation:
                    analyzed.append(GeometricSegmentationInput(path=p, kind=k))
                case AssetKind.custom_annotations:
                    analyzed.append(CustomAnnotationsInput(path=p, kind=k))
                case AssetKind.stl | AssetKind.seg | AssetKind.am:
                    sff_path = convert_app_specific_segm_to_sff(i.path)
                    analyzed.append(SFFInput(path=sff_path, kind=AssetKind.sff))
                    # TODO: remove app specific segm file?
                case AssetKind.ometiff_image:
                    analyzed.append(OMETIFFImageInput(path=p, kind=k))
                case AssetKind.ometiff_segmentation:
                    analyzed.append(OMETIFFSegmentationInput(path=p, kind=k))
                case AssetKind.tiff_image_stack_dir:
                    analyzed.append(TIFFImageStackDirInput(path=p, kind=k))
                case AssetKind.tiff_segmentation_stack_dir:
                    analyzed.append(TIFFSegmentationStackDirInput(path=p, kind=k))
                case _:
                    raise Exception(f"Input kind is not recognized. Input item: {i}")

        # print(f"pre_analyzed_inputs_list: {analyzed}")
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

    async def initialization(
        self, mode: PreprocessorMode, extra_metadata: ExtraMetadata
    ):
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
            match mode:
                case PreprocessorMode.extend:
                    new_db_path = Path(self.preprocessor_input.db_path)
                    db = FileSystemVolumeServerDB(new_db_path, store_type="zip")
                    volume_metadata = await db.read_metadata(
                        self.preprocessor_input.entry_data.source_db,
                        self.preprocessor_input.entry_data.entry_id,
                    )
                    root.attrs[METADATA_DICT_NAME] = volume_metadata.model_dump()
                    root.attrs[ANNOTATIONS_DICT_NAME] = await db.read_annotations(
                        self.preprocessor_input.entry_data.source_db,
                        self.preprocessor_input.entry_data.entry_id,
                    )

                case PreprocessorMode.add:
                    init_metadata_model = INIT_METADATA_MODEL.model_copy()
                    init_annotations_model = INIT_ANNOTATIONS_MODEL.model_copy()
                    if extra_metadata is not None:
                        init_metadata_model.extra_metadata = extra_metadata

                    root.attrs[METADATA_DICT_NAME] = init_metadata_model.model_dump()

                    root.attrs[ANNOTATIONS_DICT_NAME] = init_annotations_model.model_dump()
                case _:
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

def fix_inputs(a: GeneralPreprocessorParameters):
    for i in a.inputs:
        if i.kind == AssetKind.wrl:
            # convert wrl to stl
            stl_path = wrl_to_stl(Path(i.path), Path(a.working_folder) / Path(i.path).with_suffix('.stl')  )
            i.kind = AssetKind.stl
            i.path = stl_path
    return a

app = typer.Typer()

@app.command("preprocess")
def preprocess(
    arguments_json: str = typer.Option(default=...),
    ):
    json_path = Path(arguments_json)
    arguments_dict: object = read_json(json_path)
    arguments = GeneralPreprocessorParameters.model_validate(arguments_dict)
    # TODO: unpack to variables
    asyncio.run(
        main_preprocessor(
            a=arguments
        )
    )



app.command()(preprocess)

app.command(delete_entry)

app.command(remove_volume)

app.command(remove_segmentation)

app.command(remove_segment_annotations)

app.command(remove_descriptions)

app.command(edit_segment_annotations)

app.command(edit_descriptions)


async def main_preprocessor(
    a: GeneralPreprocessorParameters):

    a = fix_inputs(a)

    extra_metadata = ExtraMetadata()
    if a.pre_downsampling_factor:
        extra_metadata.pre_downsampling_factor = int(a.pre_downsampling_factor)
        # should not exclude extra data a
        inputs = pre_downsample_data(
            a.inputs, a.working_folder
        )
        a.inputs = inputs

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
        assert a.mode == PreprocessorMode.extend, "Preprocessor mode is not supported"

    await preprocessor.initialization(mode=a.mode, extra_metadata=extra_metadata)
    preprocessor.preprocessing()
    preprocessor.store_to_db(mode=a.mode)
    
    
    


if __name__ == "__main__":
    app()
