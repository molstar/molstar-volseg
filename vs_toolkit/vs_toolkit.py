import argparse
import asyncio
from dataclasses import astuple, fields
import io
import json
from operator import attrgetter
from cellstar_preprocessor.tools.brotli.brotli import brotli_bytes_to_file
from db.cellstar_db.models import Info
from pydantic.dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional, Protocol, Union
from zipfile import ZIP_DEFLATED, ZIP_LZMA, ZipFile

from cellstar_db.file_system.db import FileSystemVolumeServerDB
from cellstar_db.models import BaseEnum, Metadata, SegmentationKind, TimeInfo
from cellstar_query.core.service import VolumeServerService
from cellstar_query.query import (
    get_geometric_segmentation_query,
    get_meshes_bcif_query,
    get_info_query,
    get_segmentation_cell_query,
    get_volume_cell_query,
)
from cellstar_query.requests import MetadataRequest
from pydantic import BaseModel

DEFAULT_MAX_POINTS = 1000000000000
INDEX_JSON_FILENAME = "index.json"
DEFAULT_MESH_DETAIL_LVL = 5


class ContentType(BaseEnum):
    volume = "volume"
    lattice = "lattice"
    mesh = "mesh"
    geometric_segmentation = "geometric_segmentation"
    annotations = "annotations"
    metadata = "metadata"
    query = "query"

# InputData is basically all atributes of QueryTask class
# same way could be an instance of that class

class CVSXFileInfo(BaseModel):
    type: ContentType

class VolumeFileInfo(CVSXFileInfo):
    channelId: str
    timeframeIndex: int

class SegmentationFileInfo(CVSXFileInfo):
    segmentationId: str
    timeframeIndex: int

class LatticeSegmentationFileInfo(SegmentationFileInfo):
    pass

class MeshSegmentationFilesInfo(SegmentationFileInfo):
    segmentsFilenames: list[str]


class GeometricSegmentationFileInfo(SegmentationFileInfo):
    pass


# careful with meshSegmentations and geometricSegmentations

class CVSXFilesIndex(BaseModel):
    # file name to info mapping
    volumes: dict[str, VolumeFileInfo]
    # file name to info mapping
    latticeSegmentations: dict[LatticeSegmentationFileInfo] | None = None
    # file name to info mapping
    geometricSegmentations: dict[str, GeometricSegmentationFileInfo] | None = None

    # at the frontend iterate over list
    # each item is data for a single mesh segmentation set and timeframe
    # have list of filenames
    meshSegmentations: list[MeshSegmentationFilesInfo] | None = None
    # filenames
    annotations: str
    metadata: str
    query: str


class JsonQueryParams(BaseModel):
    # TODO: fix SERIALIZE ENUM?
    # also at frontend
    segmentation_kind: SegmentationKind
    entry_id: str
    source_db: str
    time: Optional[int] = None
    channel_id: Optional[str] = None
    segmentation_id: Optional[str] = None
    # TODO: maybe drop it at all and get the first available mesh resolution?
    detail_lvl: Optional[int] = None
    max_points: Optional[int] = None


class ParsedArgs(BaseModel):
    db_path: Path
    out: Path
    json_params_path: Path


def _parse_argparse_args(args: argparse.Namespace):
    return ParsedArgs(
        db_path=Path(args.db_path),
        out=Path(args.out),
        json_params_path=Path(args.json_params_path),
    )


def _parse_json_params(json_path: Path):
    with open(json_path.resolve(), "r", encoding="utf-8") as f:
        raw_json: dict = json.load(f)
        
    return JsonQueryParams.model_validate(raw_json)


# TODO: QueryResponse
class QueryTaskBase(Protocol):
    async def execute(self) -> QueryResponse: ...


class QueryTaskParams(BaseModel):
    # parsed_args:
    volume_server: VolumeServerService
    # custom_params: Optional[QuerySpecificParams]


class QueryTask(QueryTaskBase):
    def __init__(self, params: QueryTaskParams):
        # args, volume_server = params.values()
        volume_server = params["volume_server"]
        self.volume_server = volume_server


class VolumeQueryTask(QueryTask):
    def __init__(
        self,
        volume_server: VolumeServerService,
        time: int,
        channel_id: str,
        source_db: str,
        entry_id: str,
        max_points: int,
    ):
        self.volume_server = volume_server
        self.time = time
        self.channel_id = channel_id
        self.source_db = source_db
        self.entry_id = entry_id
        self.max_points = max_points

    async def execute(self):
        response = await get_volume_cell_query(
            volume_server=self.volume_server,
            source=self.source_db,
            id=self.entry_id,
            time=self.time,
            channel_id=self.channel_id,
            max_points=self.max_points,
        )
        return QueryResponse(data=response, type="volume", input_data=self.__dict__)


class LatticeSegmentationQueryTask(QueryTask):
    def __init__(
        self,
        volume_server: VolumeServerService,
        time: int,
        segmentation_id: str,
        source_db: str,
        entry_id: str,
        max_points: int,
    ):
        self.volume_server = volume_server
        self.time = time
        self.segmentation_id = segmentation_id
        self.source_db = source_db
        self.entry_id = entry_id
        self.max_points = max_points

    async def execute(self):
        response = await get_segmentation_cell_query(
            volume_server=self.volume_server,
            source=self.source_db,
            id=self.entry_id,
            time=self.time,
            segmentation=self.segmentation_id,
            max_points=self.max_points,
        )
        return QueryResponse(
            data=response, type="lattice", input_data=self.__dict__
        )


class MeshSegmentationQueryTask(QueryTask):
    def __init__(
        self,
        volume_server: VolumeServerService,
        time: int,
        segmentation_id: str,
        source_db: str,
        entry_id: str,
        detail_lvl: int,
    ):
        self.volume_server = volume_server
        self.time = time
        self.segmentation_id = segmentation_id
        self.source_db = source_db
        self.entry_id = entry_id
        # could be optional?
        self.detail_lvl = detail_lvl

    async def execute(self):
        metadata_response: Info = await get_info_query(
            volume_server=self.volume_server, source=self.source_db, id=self.entry_id
        )
        mr = metadata_response.metadata
        segment_ids = list(
            mr.segmentation_meshes.metadata[self.segmentation_id].mesh_timeframes[self.time].segment_ids.keys()
        )
        response: list[str, bytes] = []
        for segment_id in segment_ids:
            r = await get_meshes_bcif_query(
                volume_server=self.volume_server,
                segmentation_id=self.segmentation_id,
                source=self.source_db,
                id=self.entry_id,
                time=self.time,
                segment_id=segment_id,
                detail_lvl=self.detail_lvl,
            )
            response.append((str(segment_id), r))
        return QueryResponse(data=response, type="mesh", input_data=self.__dict__)


class GeometricSegmentationQueryTask(QueryTask):
    def __init__(
        self,
        volume_server: VolumeServerService,
        time: int,
        segmentation_id: str,
        source_db: str,
        entry_id: str,
    ):
        self.volume_server = volume_server
        self.time = time
        self.segmentation_id = segmentation_id
        self.source_db = source_db
        self.entry_id = entry_id

    async def execute(self):
        response = await get_geometric_segmentation_query(
            volume_server=self.volume_server,
            segmentation_id=self.segmentation_id,
            source=self.source_db,
            id=self.entry_id,
            time=self.time,
        )
        return QueryResponse(
            data=response, type="geometric-segmentation", input_data=self.__dict__
        )

@dataclass
class QueryResponse:
    # NOTE: list[tuple[str, bytes]] - list of tuples where str = segment_id, bytes - bcif
    # TODO: response is bytes or str or?
    data: Union[bytes, list[tuple[str, bytes]], str, dict]
    type: ContentType
    query_task: QueryTaskBase
    
    def __iter__(self):
        return iter(astuple(self))
    
    def __getitem__(self, keys):
        return iter(getattr(self, k) for k in keys)


def _get_channel_ids_from_metadata(grid_metadata: Metadata):
    return grid_metadata.volumes.channel_ids


def _get_volume_timeframes_from_metadata(grid_metadata: Metadata):
    start = grid_metadata.volumes.time_info.start
    end = grid_metadata.volumes.time_info.end

    return list(range(start, end + 1))



# rework this system, should data should have correct type
# depending on the response
def _write_to_file(responses: list[QueryResponse], out_path: Path):
    # should be similar to create in memory zip
    file = io.BytesIO()

    cvsx_files_index = CVSXFilesIndex(metadata=None, query=None)
    barr = bytearray()
    for r in responses:
        # do not upack
        match r.type:
            # do not know upfront the type
            case ContentType.volume:
                r: VolumeResponse
                barr.extend(r.data)     
                # compose a sting
                # channel_id = i.["channel_id"]
                # time = input_data["time"]
                # name = f"{type}_{channel_id}_{time}.bcif"
                # zip_file.writestr(name, response)
                info = VolumeFileInfo(
                    # need to make input data a model
                    channelId=input_data["channel_id"]
                )
                info: VolumeFileInfo = {
                    "channelId": channel_id,
                    "timeframeIndex": time,
                    "type": type,
                }
                if not "volumes" in cvsx_files_index:
                    cvsx_files_index["volumes"] = {}

                cvsx_files_index["volumes"][name] = info
    
    # compresss this directly, to json, and then compress
    data = cvsx_files_index.model_dump_json()
    
    # NOTE: at the end
    bstr = bytes(barr)
    
    # TODO: bstr here
    brotli_bytes_to_file(s, out_path)
    
    # # need the alternative for this
    # with ZipFile(file, "w", ZIP_LZMA) as zip_file:
    #     for r in responses:
    #         response = r.response
    #         type = r.type
    #         input_data = r.input_data

    #         if type == "volume":
    #             # name should be created based on type and input data
    #             channel_id = input_data["channel_id"]
    #             time = input_data["time"]
    #             name = f"{type}_{channel_id}_{time}.bcif"
    #             zip_file.writestr(name, response)
    #             info: VolumeFileInfo = {
    #                 "channelId": channel_id,
    #                 "timeframeIndex": time,
    #                 "type": type,
    #             }
    #             if not "volumes" in cvsx_files_index:
    #                 cvsx_files_index["volumes"] = {}

    #             cvsx_files_index["volumes"][name] = info

    #         elif type == "lattice":
    #             segmentation_id = input_data["segmentation_id"]
    #             time = input_data["time"]
    #             name = f"{type}_{segmentation_id}_{time}.bcif"

    #             info: LatticeSegmentationFileInfo = {
    #                 "timeframeIndex": time,
    #                 "type": type,
    #                 "segmentationId": segmentation_id,
    #             }
    #             if not "latticeSegmentations" in cvsx_files_index:
    #                 cvsx_files_index["latticeSegmentations"] = {}

    #             cvsx_files_index["latticeSegmentations"][name] = info

    #             zip_file.writestr(name, response)
    #         elif type == "mesh":
    #             # how to include segmentation id here?
    #             segmentation_id = input_data["segmentation_id"]
    #             time = input_data["time"]
    #             meshes: list[str, bytes] = response
    #             filenames = []
    #             for segment_id, content in meshes:
    #                 filename = f"{type}_{segment_id}_{segmentation_id}_{time}.bcif"
    #                 filenames.append(filename)
    #                 zip_file.writestr(filename, content)

    #             info: MeshSegmentationFilesInfo = {
    #                 "segmentationId": segmentation_id,
    #                 "timeframeIndex": time,
    #                 "segmentsFilenames": filenames,
    #                 "type": type,
    #             }

    #             if not "meshSegmentations" in cvsx_files_index:
    #                 cvsx_files_index["meshSegmentations"] = []

    #             cvsx_files_index["meshSegmentations"].append(info)

    #         elif type == "annotations" or type == "metadata" or type == "query":
    #             name = f"{type}.json"
    #             dumped_JSON: str = json.dumps(response, ensure_ascii=False, indent=4)
    #             zip_file.writestr(name, data=dumped_JSON)
    #             cvsx_files_index[type] = name
    #         # TODO: change geometric-segmentation
    #         elif type == "geometric-segmentation":
    #             segmentation_id = input_data["segmentation_id"]
    #             time = input_data["time"]
    #             name = f"{type}_{segmentation_id}_{time}.json"
    #             dumped_JSON: str = json.dumps(response, ensure_ascii=False, indent=4)
    #             zip_file.writestr(name, data=dumped_JSON)

    #             info: GeometricSegmentationFileInfo = {
    #                 "segmentationId": segmentation_id,
    #                 "timeframeIndex": time,
    #                 "type": type,
    #             }
    #             if not "geometricSegmentations" in cvsx_files_index:
    #                 cvsx_files_index["geometricSegmentations"] = {}

    #             cvsx_files_index["geometricSegmentations"][name] = info

    #     dumped_index_JSON: str = json.dumps(cvsx_files_index, ensure_ascii=False, indent=4)
    #     zip_file.writestr(INDEX_JSON_FILENAME, data=dumped_index_JSON)

    # print(indexJson)
    # zip_data = file.getvalue()

    # with open(str(out_path.resolve()), "wb") as f:
    #     f.write(zip_data)
    
    
   
    

def _get_timeframes_from_timeinfo(t: TimeInfo, segmentation_id: str):
    return list(range(t[segmentation_id]["start"], t[segmentation_id]["end"] + 1))


def _get_segmentation_timeinfo(
    grid_metadata: Metadata,
    kind: Literal[
        "geometric_segmentation", "segmentation_meshes", "segmentation_lattices"
    ],
):
    if kind in grid_metadata and grid_metadata[kind]["segmentation_ids"]:
        return grid_metadata[kind]["time_info"]
    else:
        return []


def _get_segmentation_ids(
    grid_metadata: Metadata,
    kind: Literal[
        "geometric_segmentation", "segmentation_meshes", "segmentation_lattices"
    ],
):
    if kind in grid_metadata and "segmentation_ids" in grid_metadata[kind]:
        return grid_metadata[kind]["segmentation_ids"]
    else:
        return []


def _query_segmentation_data(
    kind: Literal[
        "geometric_segmentation", "segmentation_meshes", "segmentation_lattices"
    ],
    parsed_params: JsonQueryParams,
    metadata: Metadata,
    volume_server: VolumeServerService,
):
    entry_id = parsed_params["entry_id"]
    source_db = parsed_params["source_db"]

    queries_list = []
    max_points = DEFAULT_MAX_POINTS
    if "max_points" in parsed_params:
        max_points = parsed_params["max_points"]

    segmentation_ids = _get_segmentation_ids(metadata, kind)
    if "segmentation_id" in parsed_params:
        segmentation_ids = [parsed_params["segmentation_id"]]

    if kind == "segmentation_lattices":
        task = LatticeSegmentationQueryTask
    elif kind == "geometric_segmentation":
        task = GeometricSegmentationQueryTask
    elif kind == "segmentation_meshes":
        task = MeshSegmentationQueryTask

    for segmentation_id in segmentation_ids:
        timeinfo = _get_segmentation_timeinfo(metadata, kind)
        timeframes = _get_timeframes_from_timeinfo(timeinfo, segmentation_id)
        if "time" in parsed_params:
            timeframes = [parsed_params["time"]]

        for timeframe in timeframes:
            if kind == "segmentation_lattices":
                queries_list.append(
                    task(
                        volume_server=volume_server,
                        time=timeframe,
                        segmentation_id=segmentation_id,
                        source_db=source_db,
                        entry_id=entry_id,
                        max_points=max_points,
                    )
                )
            elif kind == "segmentation_meshes":
                # get detail lvl here
                detail_lvl = DEFAULT_MESH_DETAIL_LVL
                if "detail_lvl" in parsed_params:
                    detail_lvl = parsed_params["detail_lvl"]
                queries_list.append(
                    task(
                        volume_server=volume_server,
                        time=timeframe,
                        segmentation_id=segmentation_id,
                        source_db=source_db,
                        entry_id=entry_id,
                        detail_lvl=detail_lvl,
                    )
                )
            else:
                queries_list.append(
                    task(
                        volume_server=volume_server,
                        time=timeframe,
                        segmentation_id=segmentation_id,
                        source_db=source_db,
                        entry_id=entry_id,
                    )
                )
    return queries_list


async def query(args: argparse.Namespace):
    # 1. Parse argparse args
    parsed_args = _parse_argparse_args(args)
    # 2. Parse json params
    params: JsonQueryParams = _parse_json_params(parsed_args["json_params_path"])

    entry_id = params.entry_id
    source_db = params.source_db

    db = FileSystemVolumeServerDB(folder=parsed_args.db_path)

    # initialize server
    volume_server = VolumeServerService(db)

    # 3. query metadata
    metadata = await volume_server.get_metadata(
        req=MetadataRequest(
            source=params.source_db, structure_id=params.entry_id
        )
    )
    grid_metadata: Metadata = metadata["grid"]
    annotations = metadata["annotation"]

    queries_list: list[QueryTaskBase] = []
    channel_ids = _get_channel_ids_from_metadata(grid_metadata)
    if "channel_id" in params:
        channel_ids = [params["channel_id"]]

    max_points = DEFAULT_MAX_POINTS
    timeframes = _get_volume_timeframes_from_metadata(grid_metadata)
    if "max_points" in params:
        max_points = params["max_points"]

    # TODO: set all timeframes to this
    # for segmentations as well
    if "time" in params:
        timeframes = [params["time"]]
        # ... mesh, shape geometric-segmentation

    for channel_id in channel_ids:
        for timeframe in timeframes:
            queries_list.append(
                VolumeQueryTask(
                    volume_server=volume_server,
                    time=timeframe,
                    channel_id=channel_id,
                    source_db=source_db,
                    entry_id=entry_id,
                    max_points=max_points,
                )
            )

    # should check each kind of segmentation, and do it just if it exists?
    lat = []
    mesh = []
    gs = []
    if (
        grid_metadata["segmentation_lattices"]
        and len(grid_metadata["segmentation_lattices"]["segmentation_ids"]) > 0
    ):
        lat = _query_segmentation_data(
            "segmentation_lattices", params, grid_metadata, volume_server
        )
    if (
        grid_metadata["segmentation_meshes"]
        and len(grid_metadata["segmentation_meshes"]["segmentation_ids"]) > 0
    ):
        mesh = _query_segmentation_data(
            "segmentation_meshes", params, grid_metadata, volume_server
        )
    if (
        grid_metadata["geometric_segmentation"]
        and len(grid_metadata["geometric_segmentation"]["segmentation_ids"]) > 0
    ):
        gs = _query_segmentation_data(
            "geometric_segmentation", params, grid_metadata, volume_server
        )

    queries_list = queries_list + lat + mesh + gs

    # NOTE: afterwards, do:
    responses: list[QueryResponse] = []
    responses.append(
        QueryResponse(data=grid_metadata, type="metadata", input_data={})
    )
    responses.append(
        QueryResponse(data=annotations, type="annotations", input_data={})
    )
    responses.append(QueryResponse(data=params, type="query", input_data={}))

    for query in queries_list:
        r = await query.execute()
        responses.append(r)

    _write_to_file(responses, parsed_args["out"])


async def main():
    # add one required argument - json
    # drop support for simple queries at all
    main_parser = argparse.ArgumentParser(add_help=True)

    # common_subparsers = main_parser.add_subparsers(title='Query type', dest='query_type', help='Select one of: ')
    # COMMON ARGUMENTS
    required_named = main_parser.add_argument_group("Required named arguments")
    required_named.add_argument("--db_path", type=str, required=True, help="Path to db")
    # TODO: exclude extension
    required_named.add_argument(
        "--out", type=str, required=True, help="Path to output file including extension"
    )
    required_named.add_argument(
        "--json-params-path",
        required=True,
        type=str,
        help="Path to .json file with query parameters",
    )

    args = main_parser.parse_args()

    await query(args)


if __name__ == "__main__":
    asyncio.run(main())
