import os
from pathlib import Path
import argparse
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from api import v1 as api_v1
from api import v2 as api_v2
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb

# initialized msg pack for numpy
import msgpack_numpy as m

from volume_server.src.preprocessed_volume_to_cif.implementations.ciftools_volume_to_cif_converter import \
    CifToolsVolumeToCifConverter
from volume_server.src.volume_server_v1 import VolumeServerV1


DEFAULT_HOST = '0.0.0.0'  # 0.0.0.0 = localhost
DEFAULT_PORT = 9000
DEFAULT_DB_PATH = Path('db')

def prepare_fastapi_app(db_path: Path):
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
    db = LocalDiskPreprocessedDb(folder=db_path)
    volume_to_cif_converter = CifToolsVolumeToCifConverter()

    # initialize server
    volume_server = VolumeServerV1(db, volume_to_cif_converter)

    api_v1.configure_endpoints(app, volume_server)
    api_v2.configure_endpoints(app, volume_server)

    return app


def initialize_server(*, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, db_path: Path = DEFAULT_DB_PATH):
    '''Initialize and run API server'''
    m.patch()

    app = prepare_fastapi_app(db_path=db_path)

    # noinspection PyTypeChecker
    uvicorn.run(app, host=host, port=port)

def parse_args() -> argparse.Namespace:
    '''Parse command line arguments for `initialize_server`'''
    parser = argparse.ArgumentParser(description='Run Volume Server API')
    parser.add_argument('--host', type=str, default=DEFAULT_HOST, help=f'Set API IP (default: {DEFAULT_HOST} (localhost))')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'Set API port (default: {DEFAULT_PORT})')
    parser.add_argument('--db_path', type=Path, default=DEFAULT_DB_PATH, help=f'Path to db (default: {DEFAULT_DB_PATH})')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    print(args)
    initialize_server(**vars(args))
