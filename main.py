from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import v1 as api
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb
from volume_server.preprocessed_volume_to_cif.implementations.ciftools_volume_to_cif_converter import \
    CifToolsVolumeToCifConverter
from volume_server.volume_server_v1 import VolumeServerV1

# initialized msg pack for numpy
import msgpack_numpy as m
m.patch()

app = FastAPI()

# origins = [
#     "http://localhost",
#     "http://localhost:9000",
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# initialize dependencies
db = LocalDiskPreprocessedDb()
volume_to_cif_converter = CifToolsVolumeToCifConverter()

# initialize server
volume_server = VolumeServerV1(db, volume_to_cif_converter)


api.configure_endpoints(app, volume_server)
