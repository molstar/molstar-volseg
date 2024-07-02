import unittest

import requests
from cellstar_server.app.tests._test_server_runner import ServerTestBase

test_configs = {
    "emdb": {
        "emd-1832": {
            "cell": {
                "segmentation": "0",
                time=0,
                "channel_id": "0",
                "max_points": 100000000,
            },
            "down_sampled": {
                "segmentation": "0",
                time=0,
                "channel_id": "0",
                "max_points": 10,
            },
        }
    }
}


# @app.get("/v1/{source}/{id}/volume/cell/{time}/{channel_id}")
class FetchVolumeTest(ServerTestBase):
    def __fetch_for_test(self, db: str, entry: str, params: dict) -> str:
        r = requests.get(
            f'{self.serverUrl()}/v1/{db}/{entry}/volume/cell/{params.get("time")}/{params.get("channel_id")}?max_points={params.get("max_points")}'
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

                        out_of_boundaries = self.__fetch_for_test(
                            db, entry_id, entry.get("cell")
                        )
                        print(
                            "[VolumeTests] Case *cell* -> received body of len : "
                            + str(len(out_of_boundaries))
                        )

                        down_sampled = self.__fetch_for_test(
                            db, entry_id, entry.get("down_sampled")
                        )
                        print(
                            "[VolumeTests] Case *down_sampled* -> received body of len : "
                            + str(len(down_sampled))
                        )

                        self.assertAlmostEqual(
                            len(out_of_boundaries) / (8 * len(down_sampled)),
                            1,
                            delta=0.4,
                        )
        finally:
            pass


# NOTE: this test won't work for segmentation probably
# because it contains set table which does not scale with downsampling
# class FetchSegmentationTest(ServerTestBase):
#     def __fetch_for_test(self, db: str, entry: str, params: dict) -> str:
#         r = requests.get(
#             # @app.get("/v1/{source}/{id}/segmentation/cell/{segmentation}/{time}")
#             f'{self.serverUrl()}/v1/{db}/{entry}/segmentation/cell/{params.get("segmentation")}/{params.get("time")}?max_points={params.get("max_points")}'
#         )
#         self.assertEqual(r.status_code, 200)
#         body = r.text
#         self.assertIsNotNone(body)
#         return body

#     def test(self):
#         try:
#             with self.server.run_in_thread():
#                 for db in test_configs.keys():
#                     entries = test_configs.get(db)
#                     for entry_id in entries.keys():
#                         entry = entries.get(entry_id)

#                         out_of_boundaries = self.__fetch_for_test(db, entry_id, entry.get("cell"))
#                         print("[VolumeTests] Case *cell* -> received body of len : " + str(len(out_of_boundaries)))

#                         down_sampled = self.__fetch_for_test(db, entry_id, entry.get("down_sampled"))
#                         print("[VolumeTests] Case *down_sampled* -> received body of len : " + str(len(down_sampled)))

#                         self.assertAlmostEqual(len(out_of_boundaries) / (8 * len(down_sampled)), 1, delta=0.4)
#         finally:
#             pass


if __name__ == "__main__":
    unittest.main()
