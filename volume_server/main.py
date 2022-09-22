from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from api import v1 as api_v1
from api import v2 as api_v2
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb

# TODO: this should not be required as we should not be serializing MSGPACK to JSON at all
# initialized msg pack for numpy
import msgpack_numpy as m

from volume_server.src.preprocessed_volume_to_cif.implementations.ciftools_volume_to_cif_converter import \
    CifToolsVolumeToCifConverter
from volume_server.src.volume_server_v1 import VolumeServerV1

from volume_server.settings import settings

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
app.add_middleware(GZipMiddleware, minimum_size=1000)

# initialize dependencies
db = LocalDiskPreprocessedDb(folder=settings.DB_PATH)
volume_to_cif_converter = CifToolsVolumeToCifConverter()

# initialize server
volume_server = VolumeServerV1(db, volume_to_cif_converter)

api_v1.configure_endpoints(app, volume_server)
api_v2.configure_endpoints(app, volume_server)