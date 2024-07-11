import asyncio
import copy
from pathlib import Path
from typing import TypedDict

import pytest
from cellstar_db.file_system.db import FileSystemVolumeServerDB
from cellstar_db.models import (
    AnnotationsMetadata,
    DescriptionData,
    ExternalReference,
    AssetKind,
    GeneralPreprocessorParameters,
    PreprocessorMode,
    RawInput,
    SegmentAnnotationData,
    SegmentationKind,
    TargetId,
)
from cellstar_preprocessor.preprocessor import main_preprocessor

TEST_DB_FOLDER = "db/cellstar_db/tests/test_data/testing_db"

TEST_ENTRY_INPUTS = [
    RawInput(
        path="test-data/preprocessor/sample_volumes/emdb/EMD-1832.map",
        kind=AssetKind.map,
    ),
    RawInput(
        path="test-data/preprocessor/sample_segmentations/emdb_sff/emd_1832.hff",
        kind=AssetKind.sff,
    ),
]

TEST_ENTRY_PREPROCESSOR_ARGUMENTS = GeneralPreprocessorParameters(
    mode=PreprocessorMode.add,
    entry_id="emd-1832",
    source_db="emdb",
    source_db_id="emd-1832",
    source_db_name="emdb",
    working_folder="db/cellstar_db/tests/test_data/testing_working_folder",
    db_path=TEST_DB_FOLDER,
    inputs=[
        RawInput(
            path="test-data/preprocessor/sample_volumes/emdb/EMD-1832.map",
            kind=AssetKind.map,
        ),
        RawInput(
            path="test-data/preprocessor/sample_segmentations/emdb_sff/emd_1832.hff",
            kind=AssetKind.sff,
        ),
    ],
    quantize_dtype_str=None,
    quantize_downsampling_levels=None,
    force_volume_dtype=None,
    max_size_per_downsampling_lvl_mb=None,
    min_size_per_downsampling_lvl_mb=None,
    min_downsampling_level=None,
    max_downsampling_level=None,
    remove_original_resolution=None,
)


@pytest.fixture(scope="module")
def testing_db():
    # create db
    test_db_path = Path(TEST_ENTRY_PREPROCESSOR_ARGUMENTS.db_path)
    if (test_db_path).is_dir() == False:
        test_db_path.mkdir(parents=True)

    db = FileSystemVolumeServerDB(folder=test_db_path, store_type="zip")

    # remove previous test entry if it exists
    exists = asyncio.run(
        db.contains(
            TEST_ENTRY_PREPROCESSOR_ARGUMENTS.source_db,
            TEST_ENTRY_PREPROCESSOR_ARGUMENTS.entry_id,
        )
    )
    if exists:
        asyncio.run(
            db.delete(
                TEST_ENTRY_PREPROCESSOR_ARGUMENTS.source_db,
                TEST_ENTRY_PREPROCESSOR_ARGUMENTS.entry_id,
            )
        )

    # create test entry with annotations
    # NOTE: for now just could be emd-1832 sff, 6 descriptions, 6 segment annotations
    # TODO: in future can add to emd-1832 map and sff also geometric segmentation
    # but for testing annotations context emd-1832 sff is sufficient
    asyncio.run(main_preprocessor(TEST_ENTRY_PREPROCESSOR_ARGUMENTS))

    yield db


FAKE_SEGMENT_ANNOTATIONS: list[SegmentAnnotationData] = [
    SegmentAnnotationData(
        id="whatever_1",
        segment_kind=SegmentationKind.lattice,
        segment_id=999999,
        segmentation_id='99999999',
        time=2222222,
        color=[0.0, 0.0, 0.0, 1.0],
    ),
    SegmentAnnotationData(
        id="whatever_2",
        segment_kind=SegmentationKind.lattice,
        segment_id=888888888,
        segmentation_id='888888888',
        time=888888888,
        color=[1.0, 1.0, 1.0, 1.0],
    ),
]

FAKE_EXTERNAL_REFERENCES_1 = [
    ExternalReference(
        accession="GO_0006260",
        description="FAKE TO BE REPLACED",
        id="51",
        label="DNA replication",
        resource="go",
        url="http://purl.obolibrary.org/obo/GO_0006260",
    ),
    ExternalReference(
        accession="GO_0030174",
        description="Any process that modulates the frequency, rate or extent of initiation of DNA-dependent DNA replication; the process in which DNA becomes competent to replicate. In eukaryotes, replication competence is established in early G1 and lost during the ensuing S phase.",
        id="52",
        label="regulation of DNA-dependent DNA replication initiation",
        resource="go",
        url="http://purl.obolibrary.org/obo/GO_0030174",
    ),
    ExternalReference(
        accession="PR_000010246",
        description="A protein that is a translation product of the human MCM4 gene or a 1:1 ortholog thereof.",
        id="53",
        label="DNA replication licensing factor MCM4",
        resource="pr",
        url="http://purl.obolibrary.org/obo/PR_000010246",
    ),
    ExternalReference(
        accession="NCIT_C33909",
        description="DNA replication licensing factor MCM4 (863 aa, ~97 kDa) is encoded by the human MCM4 gene. This protein is involved in the initiation of DNA replication.",
        id="54",
        label="DNA Replication Licensing Factor MCM4",
        resource="ncit",
        url="http://purl.obolibrary.org/obo/NCIT_C33909",
    ),
    ExternalReference(
        accession="Q26454",
        description="undefined (Drosophila melanogaster (Fruit fly))",
        id="55",
        label="MCM4_DROME",
        resource="UniProt",
        url="https://www.uniprot.org/uniprot/Q26454",
    ),
]

FAKE_EXTERNAL_REFERENCES_2 = [
    ExternalReference(
        accession="GO_0006260",
        description="The cellular metabolic process in which a cell duplicates one or more molecules of DNA. DNA replication begins when specific sequences, known as origins of replication, are recognized and bound by initiation proteins, and ends when the original DNA molecule has been completely duplicated and the copies topologically separated. The unit of replication usually corresponds to the genome of the cell, an organelle, or a virus. The template for replication can either be an existing DNA molecule or RNA.",
        id="41",
        label="DNA replication",
        resource="go",
        url="http://purl.obolibrary.org/obo/GO_0006260",
    ),
    ExternalReference(
        accession="GO_0030174",
        description="Any process that modulates the frequency, rate or extent of initiation of DNA-dependent DNA replication; the process in which DNA becomes competent to replicate. In eukaryotes, replication competence is established in early G1 and lost during the ensuing S phase.",
        id="42",
        label="regulation of DNA-dependent DNA replication initiation",
        resource="go",
        url="http://purl.obolibrary.org/obo/GO_0030174",
    ),
    ExternalReference(
        accession="PR_000010242",
        description="A protein that is a translation product of the human MCM2 gene or a 1:1 ortholog thereof.",
        id="43",
        label="DNA replication licensing factor MCM2",
        resource="pr",
        url="http://purl.obolibrary.org/obo/PR_000010242",
    ),
    ExternalReference(
        accession="NCIT_C28642",
        description="DNA replication licensing factor MCM2 (904 aa, ~102 kDa) is encoded by the human MCM2 gene. This protein plays a role in cell cycle regulation.",
        id="44",
        label="DNA Replication Licensing Factor MCM2",
        resource="ncit",
        url="http://purl.obolibrary.org/obo/NCIT_C28642",
    ),
    ExternalReference(
        accession="P49735",
        description="undefined (Drosophila melanogaster (Fruit fly))",
        id="45",
        label="MCM2_DROME",
        resource="UniProt",
        url="https://www.uniprot.org/uniprot/P49735",
    ),
]

FAKE_DESCRIPTIONS: list[DescriptionData] = [
    DescriptionData(
        id="7fbb778a-4a01-41d4-b8e2-e4ca187eb5ff",
        is_hidden=None,
        metadata=None,
        name="DNA replication licensing factor MCM4",
        target_id=TargetId(segment_id=97, segmentation_id="0"),
        target_kind=SegmentationKind.lattice,
        time=0,
        details=None,
        external_references=FAKE_EXTERNAL_REFERENCES_1,
    ),
    DescriptionData(
        id="9b590856-bd9a-4edc-9e49-c7b5af12773f",
        is_hidden=None,
        metadata=None,
        name="DNA replication licensing factor MCM2",
        target_id=TargetId(segment_id=97, segmentation_id="0"),
        target_kind=SegmentationKind.lattice,
        time=0,
        details=None,
        external_references=FAKE_EXTERNAL_REFERENCES_2,
    ),
]


class TestData(TypedDict):
    modify_annotations: list[SegmentAnnotationData]
    add_annotations: list[SegmentAnnotationData]
    # NOTE: uuid
    remove_annotations: list[str]

    modify_descriptions: list[DescriptionData]
    add_descriptions: list[DescriptionData]
    # NOTE: uuid
    remove_descriptions: list[str]


def __get_annotations(testing_db: FileSystemVolumeServerDB):
    annotations: AnnotationsMetadata = asyncio.run(
        testing_db.read_annotations(
            TEST_ENTRY_PREPROCESSOR_ARGUMENTS.source_db,
            TEST_ENTRY_PREPROCESSOR_ARGUMENTS.entry_id,
        )
    )
    return annotations


def _generate_test_data_for_modify_annotations(
    testing_db,
) -> list[SegmentAnnotationData]:
    # first get existing annotation ids from testing db
    annotations: AnnotationsMetadata = __get_annotations(testing_db)
    fake_segment_annotations = copy.deepcopy(FAKE_SEGMENT_ANNOTATIONS)
    existing_annotation_ids = [a["id"] for a in annotations["segment_annotations"]]
    first_fake_segment_annotation = fake_segment_annotations[0]
    first_fake_segment_annotation["id"] = existing_annotation_ids[0]
    second_fake_segment_annotation = fake_segment_annotations[1]
    second_fake_segment_annotation["id"] = existing_annotation_ids[1]

    return [first_fake_segment_annotation, second_fake_segment_annotation]


def _generate_test_data_for_add_annotations() -> list[SegmentAnnotationData]:
    return [FAKE_SEGMENT_ANNOTATIONS[0], FAKE_SEGMENT_ANNOTATIONS[1]]


def _generate_test_data_for_remove_annotations(testing_db) -> list[str]:
    # get ids of exisiting annotations
    annotations: AnnotationsMetadata = __get_annotations(testing_db)
    existing_annotation_ids = [a["id"] for a in annotations["segment_annotations"]]
    return [existing_annotation_ids[0], existing_annotation_ids[1]]


def _generate_test_data_for_modify_descriptions(testing_db) -> list[DescriptionData]:
    # first get existing description ids from testing db
    annotations: AnnotationsMetadata = __get_annotations(testing_db)

    fake_descriptions = copy.deepcopy(FAKE_DESCRIPTIONS)
    existing_description_ids = list(annotations["descriptions"].keys())

    first_fake_description = fake_descriptions[0]
    first_fake_description["id"] = existing_description_ids[0]

    existing_description_external_reference_id = annotations["descriptions"][
        existing_description_ids[0]
    ]["external_references"][0]["id"]
    first_fake_description["external_references"][0][
        "id"
    ] = existing_description_external_reference_id

    second_fake_description = fake_descriptions[1]
    second_fake_description["id"] = existing_description_ids[1]

    return [first_fake_description, second_fake_description]


def _generate_test_data_for_add_descriptions():
    return FAKE_DESCRIPTIONS


def _generate_test_data_for_remove_descriptions(testing_db):
    # get ids of exisiting descriptions
    annotations: AnnotationsMetadata = __get_annotations(testing_db)
    existing_description_ids = list(annotations["descriptions"].keys())
    return [existing_description_ids[0], existing_description_ids[1]]


@pytest.fixture(scope="module")
def generate_test_data(testing_db):
    test_data: TestData = {}

    test_data["modify_annotations"] = _generate_test_data_for_modify_annotations(
        testing_db
    )
    test_data["add_annotations"] = _generate_test_data_for_add_annotations()
    test_data["remove_annotations"] = _generate_test_data_for_remove_annotations(
        testing_db
    )

    test_data["modify_descriptions"] = _generate_test_data_for_modify_descriptions(
        testing_db
    )
    test_data["add_descriptions"] = _generate_test_data_for_add_descriptions()
    test_data["remove_descriptions"] = _generate_test_data_for_remove_descriptions(
        testing_db
    )

    yield testing_db, test_data
