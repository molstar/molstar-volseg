import pytest
from cellstar_db.file_system.annotations_context import AnnnotationsEditContext
from cellstar_db.models import AnnotationsMetadata
from cellstar_db.tests.conftest import TEST_ENTRY_PREPROCESSOR_INPUT


@pytest.mark.asyncio
async def test_add_descriptions(generate_test_data):
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
        await edit_annotations_context.add_or_modify_descriptions(
            test_data["add_descriptions"]
        )

        annotations_metadata_after_adding: AnnotationsMetadata = (
            await testing_db.read_annotations(
                TEST_ENTRY_PREPROCESSOR_INPUT["source_db"],
                TEST_ENTRY_PREPROCESSOR_INPUT["entry_id"],
            )
        )

        assert len(annotations_metadata_before_adding["descriptions"]) + len(
            test_data["add_descriptions"]
        ) == len(annotations_metadata_after_adding["descriptions"])

        current_descriptions = annotations_metadata_after_adding["descriptions"]

        for description in test_data["add_descriptions"]:
            # check that description in in current_descriptions
            # in dict
            assert description["id"] in current_descriptions.keys()
            # check equality of items
            assert description == current_descriptions[description["id"]]
