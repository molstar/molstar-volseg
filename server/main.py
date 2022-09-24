from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import app.api.v1 as api_v1
import app.api.v2 as api_v2
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb
from app.api.service import VolumeServerService

from app.settings import settings

print("Server Settings: ", settings.dict())

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
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=3)  # Default compresslevel=9 is veeery slow

# initialize dependencies
db = LocalDiskPreprocessedDb(folder=settings.DB_PATH)

# initialize server
volume_server = VolumeServerService(db)

api_v1.configure_endpoints(app, volume_server)
api_v2.configure_endpoints(app, volume_server)