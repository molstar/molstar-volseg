import unittest

import requests
from cellstar_server.app.tests._test_server_runner import ServerTestBase

test_configs = {
    "emdb": {
        "emd-1832": {
            "out_of_boundaries": {
                # "segmentation": '0',
                "x_min": -100000,
                "y_min": -100000,
                "z_min": -100000,
                "x_max": 100000,
                "y_max": 100000,
                "z_max": 100000,
                "max_points": 100000000,
            },
            "down_sampled": {
                # "segmentation": '0',
                "x_min": -100000,
                "y_min": -100000,
                "z_min": -100000,
                "x_max": 100000,
                "y_max": 100000,
                "z_max": 100000,
                "max_points": 10,
            },
            "8": {
                # "segmentation": 0,
                "x_min": -60,
                "y_min": -60,
                "z_min": -60,
                "x_max": 20,
                "y_max": 20,
                "z_max": 20,
                "max_points": 100000000,
            },
            "4": {
                # "segmentation": 0,
                "x_min": -20,
                "y_min": -20,
                "z_min": -20,
                "x_max": 20,
                "y_max": 20,
                "z_max": 20,
                "max_points": 100000000,
            },
            "2": {
                # "segmentation": 0,
                "x_min": 0,
                "y_min": 0,
                "z_min": 0,
                "x_max": 20,
                "y_max": 20,
                "z_max": 20,
                "max_points": 100000000,
            },
        }
    }
}


class FetchVolumeTest(ServerTestBase):
    def __fetch_for_test(self, db: str, entry: str, params: dict) -> str:
        r = requests.get(
            # @app.get("/v1/{source}/{id}/volume/box/{time}/{channel_id}/{a1}/{a2}/{a3}/{b1}/{b2}/{b3}")
            f"{self.serverUrl()}/v1/{db}/{entry}/volume/box/0/0"
            f'/{params.get("x_min")}/{params.get("y_min")}/{params.get("z_min")}'
            f'/{params.get("x_max")}/{params.get("y_max")}/{params.get("z_max")}'
            f'?max_points={params.get("max_points")}'
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
                            db, entry_id, entry.get("out_of_boundaries")
                        )
                        print(
                            "[VolumeTests] Case *out_of_boundaries* -> received body of len : "
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

                        entry.pop("out_of_boundaries")
                        entry.pop("down_sampled")

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
                                self.assertGreater(previous, case_result)

                            previous = case_result

        finally:
            pass


if __name__ == "__main__":
    unittest.main()
