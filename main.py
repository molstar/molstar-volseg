from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from api import v1 as api
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb

# initialized msg pack for numpy
import msgpack_numpy as m

from volume_server.src.preprocessed_volume_to_cif.implementations.ciftools_volume_to_cif_converter import \
    CifToolsVolumeToCifConverter
from volume_server.src.volume_server_v1 import VolumeServerV1


def prepare_fastapi_app():
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
    db = LocalDiskPreprocessedDb(folder=Path('db'))
    volume_to_cif_converter = CifToolsVolumeToCifConverter()

    # initialize server
    volume_server = VolumeServerV1(db, volume_to_cif_converter)

    api.configure_endpoints(app, volume_server)

    return app


def initialize_server():
    m.patch()

    app = prepare_fastapi_app()

    # noinspection PyTypeChecker
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == '__main__':
    initialize_server()
