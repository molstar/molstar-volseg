import pytest
from cellstar_db.file_system.annotations_context import AnnnotationsEditContext
from cellstar_db.models import AnnotationsMetadata
from cellstar_db.tests.conftest import TEST_ENTRY_PREPROCESSOR_ARGUMENTS


@pytest.mark.asyncio
async def test_modify_descriptions(generate_test_data):
    testing_db, test_data = generate_test_data
    with testing_db.edit_annotations(
        TEST_ENTRY_PREPROCESSOR_ARGUMENTS["source_db"],
        TEST_ENTRY_PREPROCESSOR_ARGUMENTS["entry_id"],
    ) as edit_annotations_context:
        edit_annotations_context: AnnnotationsEditContext
        await edit_annotations_context.add_or_modify_descriptions(
            test_data["modify_descriptions"]
        )

        annotations_metadata: AnnotationsMetadata = await testing_db.read_annotations(
            TEST_ENTRY_PREPROCESSOR_ARGUMENTS["source_db"],
            TEST_ENTRY_PREPROCESSOR_ARGUMENTS["entry_id"],
        )
        current_descriptions = annotations_metadata["descriptions"]

        for description in test_data["modify_descriptions"]:
            # check that description id exists in current descriptions
            assert description["id"] in current_descriptions.keys()
            # check that description from test data is equal to the
            # description from modify descriptions
            # they will not be equal since it adds external references
            # it should check not the equality
            # but the fact that previous description + test_data description
            # equals to current description

            # or rather the fact that each field of test_data description
            # equals to the field with the same name of current descriptions
            # except External references
            # to be handled separately
            # assert description == current_descriptions[description['id']]

            # checks each field of modify annotations
            # if it is equal to the field with the same name of that annotation from current annotations
            for field_name in description:
                if field_name != "external_references":
                    assert (
                        current_descriptions[description["id"]][field_name]
                        == description[field_name]
                    )
                # TODO: check external references
                else:
                    # plan:
                    # should work such that external references from description
                    # kind of overlap of two sets
                    # NOTE:
                    # iterate over refs
                    for ref in description["external_references"]:
                        # should check each ref field in description
                        # if it is equal to that ref field in
                        # current_descriptions[description['id']][field_name]

                        ref_id = ref["id"]
                        # TODO: find ref with that id
                        existing_refs = current_descriptions[description["id"]][
                            "external_references"
                        ]
                        filter_results = list(
                            filter(lambda r: r["id"] == ref_id, existing_refs)
                        )
                        assert len(filter_results) == 1
                        target_existing_ref = filter_results[0]
                        for ref_field_name in ref:
                            assert (
                                ref[ref_field_name]
                                == target_existing_ref[ref_field_name]
                            )

                            # then assert that ref[field_name] == target_existing_ref[field_name]
                            # assert ref[field_name] ==

                    # make it fail
                    # here check it
                    # 5 external references before
                    # 5 was added, but one with existing ref id
                    # 9 after
                    # correct result

        # for annotation in test_data['modify_descriptions']:
        #     filter_results = list(filter(lambda a: a['id'] == annotation['id'], current_descriptions))
        #     assert len(filter_results) == 1
        #     existing_annotation = filter_results[0]
        #     # check if those are equal
        #     assert existing_annotation == annotation
