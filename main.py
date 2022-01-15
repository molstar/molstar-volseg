from fastapi import FastAPI
from api import v1 as api
from volume_server.volume_server import VolumeServer

app = FastAPI()
volume_server = VolumeServer()


api.configure_endpoints(app, volume_server)
