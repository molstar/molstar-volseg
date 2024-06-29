import pytest
from cellstar_db.file_system.annotations_context import AnnnotationsEditContext
from cellstar_db.models import AnnotationsMetadata
from cellstar_db.tests.conftest import TEST_ENTRY_PREPROCESSOR_ARGUMENTS


@pytest.mark.asyncio
async def test_remove_annotations(generate_test_data):
    testing_db, test_data = generate_test_data
    annotations_metadata_before_removing: AnnotationsMetadata = (
        await testing_db.read_annotations(
            TEST_ENTRY_PREPROCESSOR_ARGUMENTS["source_db"],
            TEST_ENTRY_PREPROCESSOR_ARGUMENTS["entry_id"],
        )
    )
    with testing_db.edit_annotations(
        TEST_ENTRY_PREPROCESSOR_ARGUMENTS["source_db"],
        TEST_ENTRY_PREPROCESSOR_ARGUMENTS["entry_id"],
    ) as edit_annotations_context:
        edit_annotations_context: AnnnotationsEditContext
        await edit_annotations_context.remove_segment_annotations(
            test_data["remove_annotations"]
        )

        # check that annotations were removed
        # i.e. if length of annotations list decreased by length of test_data['remove_annotations']
        annotations_metadata_after_removing: AnnotationsMetadata = (
            await testing_db.read_annotations(
                TEST_ENTRY_PREPROCESSOR_ARGUMENTS["source_db"],
                TEST_ENTRY_PREPROCESSOR_ARGUMENTS["entry_id"],
            )
        )

        assert len(annotations_metadata_before_removing["segment_annotations"]) - len(
            test_data["remove_annotations"]
        ) == len(annotations_metadata_after_removing["segment_annotations"])

        current_annotations = annotations_metadata_after_removing["segment_annotations"]
        current_annotation_ids = [a["id"] for a in current_annotations]
        # here check that annotation with ids from remove annotations
        # are no longer present
        for annotation_id in test_data["remove_annotations"]:
            assert annotation_id not in current_annotation_ids
