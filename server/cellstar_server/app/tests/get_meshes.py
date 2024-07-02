import unittest

import requests
from cellstar_server.app.tests._test_server_runner import ServerTestBase

# test_configs = {
#     "empiar": {"empiar-10070": {"2": {"segmentation": 1, "detail_lvl": 2}, "1": {"segmentation": 1, "detail_lvl": 1}}}
# }


test_configs = {
    "empiar": {
        "empiar-10070": {
            "5": {segmentation_id="0", segment_id=1, "detail_lvl": 5, time=0},
            "1": {segmentation_id="0", segment_id=1, "detail_lvl": 1, time=0},
        }
    }
}


# @app.get("/v1/{source}/{id}/mesh/{segmentation_id}/{time}/{segment_id}/{detail_lvl}")
class FetchMeshesTest(ServerTestBase):
    def __fetch_for_test(self, db: str, entry: str, params: dict) -> str:
        r = requests.get(
            # f'{self.serverUrl()}/v1/{db}/{entry}/mesh/{params.get("segmentation")}/{params.get("detail_lvl")}'
            f'{self.serverUrl()}/v1/{db}/{entry}/mesh/{params.get("segmentation_id")}/{params.get("time")}/{params.get("segment_id")}/{params.get("detail_lvl")}'
        )
        self.assertEqual(r.status_code, 200)
        body = r.text
        self.assertIsNotNone(body)
        return body

    def test(self):
        try:
            with self.server.run_in_thread():
                for db in test_configs.keys():
                    entries = test_configs.get(db)
                    for entry_id in entries.keys():
                        entry = entries.get(entry_id)

                        case_results = []
                        for case in entry.keys():
                            case_response = self.__fetch_for_test(
                                db, entry_id, entry.get(case)
                            )
                            case = int(case)
                            print(
                                "case "
                                + str(case)
                                + " has len: "
                                + str(len(case_response))
                            )
                            case_results.append(len(case_response))

                        previous = None
                        for case_result in case_results:
                            if previous is not None:
                                self.assertLess(previous, case_result)

                            previous = case_result

        finally:
            pass


class FetchMeshesBcifTest(ServerTestBase):
    def __fetch_for_test(self, db: str, entry: str, params: dict) -> str:
        r = requests.get(
            # f'{self.serverUrl()}/v1/{db}/{entry}/mesh_bcif/{params.get("segmentation")}/{params.get("detail_lvl")}'
            f'{self.serverUrl()}/v1/{db}/{entry}/mesh_bcif/{params.get("segmentation_id")}/{params.get("time")}/{params.get("segment_id")}/{params.get("detail_lvl")}'
        )
        self.assertEqual(r.status_code, 200)
        body = r.text
        self.assertIsNotNone(body)
        return body

    def test(self):
        try:
            with self.server.run_in_thread():
                for db in test_configs.keys():
                    entries = test_configs.get(db)
                    for entry_id in entries.keys():
                        entry = entries.get(entry_id)

                        case_results = []
                        for case in entry.keys():
                            case_response = self.__fetch_for_test(
                                db, entry_id, entry.get(case)
                            )
                            case = int(case)
                            print(
                                "case "
                                + str(case)
                                + " has len: "
                                + str(len(case_response))
                            )
                            case_results.append(len(case_response))

                        previous = None
                        for case_result in case_results:
                            if previous is not None:
                                self.assertLess(previous, case_result)

                            previous = case_result

        finally:
            pass


if __name__ == "__main__":
    unittest.main()
