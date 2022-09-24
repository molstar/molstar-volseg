import contextlib
import threading
import time
import unittest
from abc import ABC

import uvicorn
from uvicorn import Config

from main import app


class TestServerRunner(uvicorn.Server):
    @contextlib.contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()


class ServerTestBase(ABC, unittest.TestCase):
    server = None
    app = None

    ip = "127.0.0.1"
    port = 5000

    @staticmethod
    def serverUrl():
        return f"http://{ServerTestBase.ip}:{str(ServerTestBase.port)}"

    @classmethod
    def setUpClass(cls):
        ServerTestBase.app = app
        config = Config(
            ServerTestBase.app, host=ServerTestBase.ip, port=ServerTestBase.port, log_level="info", loop="asyncio"
        )
        ServerTestBase.server = TestServerRunner(config=config)
