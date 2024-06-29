import pytest
from cellstar_db.file_system.annotations_context import AnnnotationsEditContext
from cellstar_db.models import AnnotationsMetadata
from cellstar_db.tests.conftest import TEST_ENTRY_PREPROCESSOR_ARGUMENTS


@pytest.mark.asyncio
async def test_modify_annotations(generate_test_data):
    testing_db, test_data = generate_test_data
    with testing_db.edit_annotations(
        TEST_ENTRY_PREPROCESSOR_ARGUMENTS["source_db"],
        TEST_ENTRY_PREPROCESSOR_ARGUMENTS["entry_id"],
    ) as edit_annotations_context:
        edit_annotations_context: AnnnotationsEditContext
        await edit_annotations_context.add_or_modify_segment_annotations(
            test_data["modify_annotations"]
        )

        annotations_metadata: AnnotationsMetadata = await testing_db.read_annotations(
            TEST_ENTRY_PREPROCESSOR_ARGUMENTS["source_db"],
            TEST_ENTRY_PREPROCESSOR_ARGUMENTS["entry_id"],
        )
        current_annotations = annotations_metadata["segment_annotations"]

        for annotation in test_data["modify_annotations"]:
            filter_results = list(
                filter(lambda a: a["id"] == annotation["id"], current_annotations)
            )
            assert len(filter_results) == 1
            existing_annotation = filter_results[0]
            # checks each field of modify annotations
            # if it is equal to the field with the same name of that annotation from current annotations
            for field_name in annotation:
                assert existing_annotation[field_name] == annotation[field_name]
