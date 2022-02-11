from fastapi import FastAPI
from api import v1 as api
from db.implementations.fake.fake_preprocessed_db import FakePreprocessedDb
from volume_server.fake_volume_server import FakeVolumeServer
from volume_server.preprocessed_volume_to_cif.fake_volume_to_cif_converter import FakeVolumeToCifConverter

app = FastAPI()

# initialize dependencies
db = FakePreprocessedDb()
volume_to_cif_converter = FakeVolumeToCifConverter()

# initialize server
volume_server = FakeVolumeServer(db, volume_to_cif_converter)


api.configure_endpoints(app, volume_server)
