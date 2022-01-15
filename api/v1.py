from fastapi import FastAPI
from volume_server.i_volume_server import IVolumeServer


def configure_endpoints(app: FastAPI, volume_server: IVolumeServer):
    @app.get("/")
    async def root():
        return volume_server.root()

    @app.get("/hello/{name}")
    async def say_hello(name: str):
        return volume_server.say_hello(name)
