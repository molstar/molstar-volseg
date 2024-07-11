import cellstar_server.app.api.v1 as api_v1
from cellstar_db.file_system.db import FileSystemVolumeServerDB
from cellstar_query.core.service import VolumeServerService
from cellstar_server.app.settings import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

print("Server Settings: ", settings.model_dump())

description = f"""
GIT TAG: {settings.GIT_TAG}
GIT SHA: {settings.GIT_SHA}
"""

app = FastAPI(description=description)

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
app.add_middleware(
    GZipMiddleware, minimum_size=1000, compresslevel=3
)  # Default compresslevel=9 is veeery slow

# initialize dependencies
db = FileSystemVolumeServerDB(folder=settings.DB_PATH)

# initialize server
volume_server = VolumeServerService(db)

# api_v1.configure_endpoints(app, volume_server)
api_v1.configure_endpoints(app, volume_server)
