import pytest
from cellstar_db.file_system.annotations_context import AnnnotationsEditContext
from cellstar_db.models import AnnotationsMetadata
from cellstar_db.tests.conftest import TEST_ENTRY_PREPROCESSOR_INPUT


@pytest.mark.asyncio
async def test_remove_descriptions(generate_test_data):
    testing_db, test_data = generate_test_data
    annotations_metadata_before_removing: AnnotationsMetadata = (
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
        await edit_annotations_context.remove_descriptions(
            test_data["remove_descriptions"]
        )

        # check that annotations were removed
        # i.e. if length of annotations list decreased by length of test_data['remove_descriptions']
        annotations_metadata_after_removing: AnnotationsMetadata = (
            await testing_db.read_annotations(
                TEST_ENTRY_PREPROCESSOR_INPUT["source_db"],
                TEST_ENTRY_PREPROCESSOR_INPUT["entry_id"],
            )
        )

        assert len(annotations_metadata_before_removing["descriptions"]) - len(
            test_data["remove_descriptions"]
        ) == len(annotations_metadata_after_removing["descriptions"])

        current_descriptions = annotations_metadata_after_removing["descriptions"]
        current_description_ids = list(current_descriptions.keys())
        # here check that descriptions with ids from remove annotations
        # are no longer present
        for description_id in test_data["remove_descriptions"]:
            assert description_id not in current_description_ids
