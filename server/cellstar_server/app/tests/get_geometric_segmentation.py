import requests
from cellstar_server.app.tests._test_server_runner import ServerTestBase

# no params

# test_configs = {
#     # "empiar": {"empiar-1.rec-geometric_segmentation": {
#     #     # "0": {"segmentation_id": "0"}
#     #     }}
# }

# function to fetch metadata
# get the first available id
# and create test config


class FetchGeometricSegmentationTest(ServerTestBase):
    def __create_test_configs(self):
        # another
        r = requests.get(f"{self.serverUrl()}/v1/empiar/empiar-11756/metadata/")
        self.assertEqual(r.status_code, 200)
        body: dict = dict(r.json())
        self.assertIsNotNone(body)

        # check grid metadata
        grid_metadata = body.get("grid")
        self.assertIsNotNone(grid_metadata)
        grid_metadata: dict = dict(grid_metadata)

        segmentation_id = grid_metadata.get("geometric_segmentation").get(
            "segmentation_ids"
        )[0]

        test_configs = {
            "empiar": {
                "empiar-11756": {
                    segmentation_id: {"segmentation_id": segmentation_id, "time": 0},
                }
            }
        }

        return test_configs

    def __fetch_for_test(self, db: str, entry: str, params: dict) -> str:
        r = requests.get(
            # @app.get("/v1/{source}/{id}/geometric_segmentation/{segmentation_id}")
            f'{self.serverUrl()}/v1/{db}/{entry}/geometric_segmentation/{params.get("segmentation_id")}/{params.get("time")}'
        )
        self.assertEqual(r.status_code, 200)
        body = r.text
        self.assertIsNotNone(body)
        return body

    def test(self):
        try:
            with self.server.run_in_thread():
                test_configs = self.__create_test_configs()
                for db in test_configs.keys():
                    entries = test_configs.get(db)
                    for entry_id in entries.keys():
                        entry = entries.get(entry_id)

                        for case in entry.keys():
                            case_response = self.__fetch_for_test(
                                db, entry_id, entry.get(case)
                            )
                            print(
                                "case " + case + " has len: " + str(len(case_response))
                            )
                            # self.assertIsNotNone(case_response)

        finally:
            pass
