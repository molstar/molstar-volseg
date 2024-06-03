import pytest
from cellstar_db.file_system.annotations_context import AnnnotationsEditContext
from cellstar_db.models import AnnotationsMetadata
from cellstar_db.tests.conftest import TEST_ENTRY_PREPROCESSOR_INPUT


@pytest.mark.asyncio
async def test_add_annotations(generate_test_data):
    testing_db, test_data = generate_test_data
    annotations_metadata_before_adding: AnnotationsMetadata = (
        await testing_db.read_annotations(
            TEST_ENTRY_PREPROCESSOR_INPUT["source_db"],
            TEST_ENTRY_PREPROCESSOR_INPUT["entry_id"],
        )
    )
    with testing_db.edit_annotations(
        TEST_ENTRY_PREPROCESSOR_INPUT["source_db"],
        TEST_ENTRY_PREPROCESSOR_INPUT["entry_id"],
    ) as edit_annotations_context:
        edit_annotations_context: AnnnotationsEditContext
        await edit_annotations_context.add_or_modify_segment_annotations(
            test_data["add_annotations"]
        )

        # check that annotations were added
        # i.e. if length of annotations list increased by length of test_data['add_annotations']
        annotations_metadata_after_adding: AnnotationsMetadata = (
            await testing_db.read_annotations(
                TEST_ENTRY_PREPROCESSOR_INPUT["source_db"],
                TEST_ENTRY_PREPROCESSOR_INPUT["entry_id"],
            )
        )

        assert len(annotations_metadata_before_adding["segment_annotations"]) + len(
            test_data["add_annotations"]
        ) == len(annotations_metadata_after_adding["segment_annotations"])

        current_annotations = annotations_metadata_after_adding["segment_annotations"]

        for annotation in test_data["add_annotations"]:
            # here just check that annotation is in current_annotations
            assert annotation in current_annotations
