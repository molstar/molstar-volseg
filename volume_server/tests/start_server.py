import unittest

from fastapi import FastAPI

from volume_server.tests._test_server_runner import ServerTestBase


class StartServer(ServerTestBase):
    started: bool
    shutdown: bool

    def test(self):
        self.started = False
        self.shutdown = False

        @self.app.on_event("startup")
        async def startup_event():
            self.started = True

        @self.app.on_event("shutdown")
        async def startup_event():
            self.shutdown = True

        try:
            with self.server.run_in_thread():
                self.assertTrue(self.started, "Server failed to start.")
        finally:
            self.assertTrue(self.shutdown, "Server failed to shutdown.")


if __name__ == '__main__':
    unittest.main()
