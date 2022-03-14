from fastapi import FastAPI
from api import v1 as api
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb
from volume_server.preprocessed_volume_to_cif.fake_volume_to_cif_converter import FakeVolumeToCifConverter
from volume_server.volume_server_v1 import VolumeServerV1

app = FastAPI()

# initialize dependencies
db = LocalDiskPreprocessedDb()
volume_to_cif_converter = FakeVolumeToCifConverter()

# initialize server
volume_server = VolumeServerV1(db, volume_to_cif_converter)


api.configure_endpoints(app, volume_server)
