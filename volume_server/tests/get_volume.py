import json
import unittest

import requests

from volume_server.tests._test_server_runner import ServerTestBase


class FetchVolumeTest(ServerTestBase):
    def test(self):
        try:
            with self.server.run_in_thread():
                r = requests.get(f'{self.serverUrl()}/v1/emdb/emd-1832/box/0/-100/-100/-100/50/50/50/1000')
                self.assertEqual(r.status_code, 200)
                body: dict = dict(r.json())
                self.assertIsNotNone(body)
                print("Received body: " + str(body))

        finally:
            pass


if __name__ == '__main__':
    unittest.main()
