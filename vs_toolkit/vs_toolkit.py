import argparse
import asyncio
from enum import Enum
import io
import json
from pathlib import Path
from cellstar_db.models import Asset, ModelArbitraryTypes
from cellstar_preprocessor.tools.write_in_memory_zip.write_in_memory_zip import write_in_memory_zip
from typing_extensions import Any, Literal, Optional, Protocol, TypedDict, Union
from zipfile import ZIP_DEFLATED, ZipFile
from molviewspec.builder import create_builder, Root
from molviewspec.nodes import ParseFormatT
# from ...mvs_volseg.molviewspec.molviewspec.builder import create_builder, Root
# from ...mvs_volseg.molviewspec.molviewspec.nodes import ParseFormatT
# TODO: below are the correct imports assuming that volseg MVS PR is merged
# from molviewspec.builder import create_builder, Root 
# from molviewspec.nodes import ParseFormatT

# TODO: refactor to separate files
# app.py, models.py, query.py, helpers.py, other if needed

from cellstar_db.file_system.db import FileSystemVolumeServerDB
from cellstar_db.models import Metadata, TimeInfo
from cellstar_query.core.service import VolumeServerService
from cellstar_query.query import (
    get_geometric_segmentation_query,
    get_meshes_bcif_query,
    get_metadata_query,
    get_segmentation_cell_query,
    get_volume_cell_query,
)
from cellstar_query.requests import MetadataRequest
from pydantic import BaseModel, ConfigDict, Field

DEFAULT_MAX_POINTS = 1000000000000
CVSX_INDEX_JSON_FILENAME = "index.json"
DEFAULT_MESH_DETAIL_LVL = 5
MVSJ_INDEX_JSON_FILENAME = "index.mvsj"

ResponseTypesWithJSONOutputT = Literal['annotations', 'metadata', 'query']
ResponseTypesWithJSONOutputL = ['annotations', 'metadata', 'query']

class QueryResponse(BaseModel):
    # NOTE: list[tuple[str, bytes]] - list of tuples where str = segment_id, bytes - bcif
    # TODO: response is bytes or str or?
    response: Union[bytes, list[tuple[str, bytes]], str, dict]
    type: Literal[
        "volume",
        "lattice",
        "mesh",
        "geometric-segmentation",
        "annotations",
        "metadata",
        "query",
    ]
    # TODO: model for this?
    input_data: dict

class CVSXFileInfo(BaseModel):
    type: Literal[
        "volume",
        "lattice",
        "mesh",
        "geometric-segmentation",
        "annotations",
        "metadata",
        "query",
    ]


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

# Pydantic model does not work here, check why (some attr is with tuple or?)
# IndexError: tuple index out of range
# because of using [] to assign attrs apparently
class CVSXFilesIndex(TypedDict):
    # file name to info mapping
    volumes: dict[str, VolumeFileInfo]
    # file name to info mapping
    latticeSegmentations: dict[LatticeSegmentationFileInfo] | None
    # file name to info mapping
    geometricSegmentations: dict[str, GeometricSegmentationFileInfo] | None

    # at the frontend iterate over list
    # each item is data for a single mesh segmentation set and timeframe
    # have list of filenames
    meshSegmentations: list[MeshSegmentationFilesInfo] | None
    # filenames
    annotations: str
    metadata: str
    query: str

class VolumeAsset(ModelArbitraryTypes):
    # data: io.TextIOWrapper
    data: bytes
    filename: str

class JSONAsset(ModelArbitraryTypes):
    data: str
    filename: str


# TODO: BaseModel here produces IndexError: tuple index out of range
class MVSXAssets(TypedDict):
    metadata_asset: JSONAsset
    annotations_asset: JSONAsset
    volume_assets: list[VolumeAsset]
    query_asset: JSONAsset
    cvsx_index: CVSXFilesIndex

class JsonQueryParams(BaseModel):
    segmentation_kind: Optional[Literal["mesh", "lattice", "geometric-segmentation"]]
    entry_id: str
    source_db: str
    time: Optional[int]
    channel_id: Optional[str]
    segmentation_id: Optional[str]
    # TODO: maybe drop it at all and get the first available mesh resolution?
    detail_lvl: Optional[int]
    max_points: Optional[int]


class OutputFormatsEnum(Enum):
    mvsx = 'mvsx'
    cvsx = 'cvsx'

class ParsedArgs(BaseModel):
    db_path: Path
    out: Path
    json_params_path: Path
    format: OutputFormatsEnum

def _parse_argparse_args(args: argparse.Namespace):
    # TODO: validate similar to query app
    return ParsedArgs(
        db_path=Path(args.db_path),
        out=Path(args.out),
        json_params_path=Path(args.json_params_path),
        format=str(args.format)
    )


def _parse_json_params(json_path: Path):
    return JsonQueryParams.parse_file(json_path)
    # with open(json_path.resolve(), "r", encoding="utf-8") as f:
    #     raw_json: JsonQueryParams = JsonQueryParams.parse_file.load(f)

    # return raw_json


# TODO: QueryResponse
class QueryTaskBase(Protocol):
    async def execute(self) -> QueryResponse: ...


class QueryTaskParams(ModelArbitraryTypes):
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
        return QueryResponse(response=response, type="volume", input_data=self.__dict__)


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
            response=response, type="lattice", input_data=self.__dict__
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
        metadata_response = await get_metadata_query(
            volume_server=self.volume_server, source=self.source_db, id=self.entry_id
        )
        mr: Metadata = metadata_response["grid"]
        # detail_lvl = int(sorted(mr['segmentation_meshes']['segmentation_metadata'][self.segmentation_id]['detail_lvl_to_fraction'].keys())[0])
        segment_ids = list(
            mr["segmentation_meshes"]["segmentation_metadata"][self.segmentation_id][
                "mesh_timeframes"
            ][str(self.time)]["segment_ids"].keys()
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
        return QueryResponse(response=response, type="mesh", input_data=self.__dict__)


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
            response=response, type="geometric-segmentation", input_data=self.__dict__
        )


def _get_channel_ids_from_metadata(grid_metadata: Metadata):
    return grid_metadata["volumes"]["channel_ids"]


def _get_volume_timeframes_from_metadata(grid_metadata: Metadata):
    start = grid_metadata["volumes"]["time_info"]["start"]
    end = grid_metadata["volumes"]["time_info"]["end"]

    return list(range(start, end + 1))

def _json_response_to_asset(r: QueryResponse, indexJson: CVSXFilesIndex):
    type = r.type
    response = r.response
    assert type in ResponseTypesWithJSONOutputL, f'Response type {type} is not supported by this function'
    
    # name should be created based on type and input data
    name = f"{type}.json"
    indexJson[type] = name
    dumped_JSON: str = json.dumps(response, ensure_ascii=False, indent=4)
    asset = JSONAsset(
        data=dumped_JSON,
        filename=name
    )
    return asset, indexJson

def _volume_response_to_asset(r: QueryResponse, indexJson: CVSXFilesIndex):
    t = r.type
    response = r.response
    input_data = r.input_data
    assert t == 'volume', f'Response type {t} is not supported by this function'
    
    # name should be created based on type and input data
    channel_id = input_data["channel_id"]
    time = input_data["time"]
    name = f"{t}_{channel_id}_{time}.bcif"
    asset = VolumeAsset(
        data=response,
        filename=name
    )
    
    info: VolumeFileInfo = {
        "channelId": channel_id,
        "timeframeIndex": time,
        "type": t,
    }
    if not "volumes" in indexJson:
        indexJson["volumes"] = {}

    indexJson["volumes"][name] = info
    
    return asset, indexJson

def _create_assets(responses: list[QueryResponse], indexJson: CVSXFilesIndex):
    volume_assets: list[VolumeAsset] = []
    for r in responses:
        # TODO: use metadata for segmentation node
        type = r.type
        match type:
            case 'volume':
                volume_asset, indexJson = _volume_response_to_asset(r, indexJson)
                volume_assets.append(volume_asset)
            case 'metadata':
                metadata_asset, indexJson = _json_response_to_asset(r, indexJson)
            case 'annotations':
                annotations_asset, indexJson = _json_response_to_asset(r, indexJson)
            case 'query':
                query_asset, indexJson = _json_response_to_asset(r, indexJson)
            case _:
                raise Exception('Response type: ' + type + ' is not supported yet.')
            
    msvx_assets = MVSXAssets(
        volume_assets=volume_assets,
        cvsx_index=indexJson,
        metadata_asset=metadata_asset,
        annotations_asset=annotations_asset,
        query_asset=query_asset
        )
    return msvx_assets  

def _create_mvsj_tree_builder(assets: MVSXAssets, assets_folder_name: str):
    builder = create_builder()
    if assets['volume_assets'] is not None:
        volume_assets = assets['volume_assets']
        for va in volume_assets:
            (
               builder.download(url=f'./{assets_folder_name}/{va.filename}')
                #    TODO: new format
                .parse(format='vs-density')
                # TODO: new node + new params
                .vs_volume()
                # TODO: new parent for volume_representation and related functionality
                .volume_representation(type="isosurface")
                .color(color='aqua')
            )
    # TODO: segmentations, geometric etc.
            
    return builder
    

def _create_index_mvsj(assets: MVSXAssets, assets_folder_name: str):
    builder = _create_mvsj_tree_builder(assets, assets_folder_name)
    return builder.get_state()
    


def _create_mvsx(mvsx_assets: MVSXAssets, index_mvsj_json_str: str, out_path: Path, assets_folder_name: str):
    # file = io.BytesIO()
    # with ZipFile(file, "w", ZIP_DEFLATED) as zip_file:
    #     dumped_cvsx_index_JSON: str = json.dumps(mvsx_assets['cvsx_index'], ensure_ascii=False, indent=4)
    #     # TODO: check if works
    #     # TODO: other assets
    #     if mvsx_assets['volume_assets'] is not None:
    #         for va in mvsx_assets['volume_assets']:
    #             zip_file.writestr(f'{assets_folder_name}/{va.filename}', data=va.data)
            
    #     zip_file.writestr(f'{assets_folder_name}/{CVSX_INDEX_JSON_FILENAME}', data=dumped_cvsx_index_JSON)
    #     zip_file.writestr(MVSJ_INDEX_JSON_FILENAME, data=index_mvsj_json_str)
        
    #     zip_data = file.getvalue()

    assert out_path.suffix == '.mvsx'

    #     with open(str(out_path.resolve()), "wb") as f:
    #         f.write(zip_data)
    assets: list[Asset] = []
    
    # CVSX index
    cvsx_index = Asset(
        filename=f'{assets_folder_name}/{CVSX_INDEX_JSON_FILENAME}',
        data=json.dumps(mvsx_assets['cvsx_index'], ensure_ascii=False, indent=4)
    )
    assets.append(cvsx_index)
    
    # MVSJ index
    mvsj_index = Asset(
        filename=MVSJ_INDEX_JSON_FILENAME,
        data=index_mvsj_json_str
    )
    assets.append(mvsj_index)
    
    # Volume data
    if mvsx_assets['volume_assets'] is not None:
        for va in mvsx_assets['volume_assets']:
            assets.append(
                Asset(
                    # TODO: check if works
                    filename=f'{assets_folder_name}/{va.filename}',
                    data=va.data
                )
            )
            
    
    
    write_in_memory_zip(output_path=out_path, assets=assets)

def _write_mvsx_to_file(responses: list[QueryResponse], indexJson: CVSXFilesIndex, out_path: Path, assets_folder_name: str):
    """
    Only works for a volume query 
    """
    assets = _create_assets(responses, indexJson)
    index_mvsj_json_str = _create_index_mvsj(assets, assets_folder_name)
    mvsx_file = _create_mvsx(assets, index_mvsj_json_str, out_path, assets_folder_name)
    return mvsx_file
    
# def _write_mvsx_to_file(file: io.BytesIO, responses: list[QueryResponse], indexJson: CVSXFilesIndex, out_path: Path):
    # _to_mvsx(responses, indexJson, out_path, 'assets')

def _write_cvsx_to_file(file: io.BytesIO, responses: list[QueryResponse], indexJson: CVSXFilesIndex, out_path: Path):
    with ZipFile(file, "w", ZIP_DEFLATED) as zip_file:
        for r in responses:
            response = r.response
            type = r.type
            input_data = r.input_data

            if type == "volume":
                # name should be created based on type and input data
                channel_id = input_data["channel_id"]
                time = input_data["time"]
                name = f"{type}_{channel_id}_{time}.bcif"
                zip_file.writestr(name, response)
                info: VolumeFileInfo = {
                    "channelId": channel_id,
                    "timeframeIndex": time,
                    "type": type,
                }
                if not "volumes" in indexJson:
                    indexJson["volumes"] = {}

                indexJson["volumes"][name] = info

            elif type == "lattice":
                segmentation_id = input_data["segmentation_id"]
                time = input_data["time"]
                name = f"{type}_{segmentation_id}_{time}.bcif"

                info: LatticeSegmentationFileInfo = {
                    "timeframeIndex": time,
                    "type": type,
                    "segmentationId": segmentation_id,
                }
                if not "latticeSegmentations" in indexJson:
                    indexJson["latticeSegmentations"] = {}

                indexJson["latticeSegmentations"][name] = info

                zip_file.writestr(name, response)
            elif type == "mesh":
                # how to include segmentation id here?
                segmentation_id = input_data["segmentation_id"]
                time = input_data["time"]
                meshes: list[str, bytes] = response
                filenames = []
                for segment_id, content in meshes:
                    filename = f"{type}_{segment_id}_{segmentation_id}_{time}.bcif"
                    filenames.append(filename)
                    zip_file.writestr(filename, content)

                info: MeshSegmentationFilesInfo = {
                    "segmentationId": segmentation_id,
                    "timeframeIndex": time,
                    "segmentsFilenames": filenames,
                    "type": type,
                }

                if not "meshSegmentations" in indexJson:
                    indexJson["meshSegmentations"] = []

                indexJson["meshSegmentations"].append(info)

            elif type == "annotations" or type == "metadata" or type == "query":
                name = f"{type}.json"
                dumped_JSON: str = json.dumps(response, ensure_ascii=False, indent=4)
                zip_file.writestr(name, data=dumped_JSON)
                indexJson[type] = name
            elif type == "geometric-segmentation":
                segmentation_id = input_data["segmentation_id"]
                time = input_data["time"]
                name = f"{type}_{segmentation_id}_{time}.json"
                dumped_JSON: str = json.dumps(response, ensure_ascii=False, indent=4)
                zip_file.writestr(name, data=dumped_JSON)

                info: GeometricSegmentationFileInfo = {
                    "segmentationId": segmentation_id,
                    "timeframeIndex": time,
                    "type": type,
                }
                if not "geometricSegmentations" in indexJson:
                    indexJson["geometricSegmentations"] = {}

                indexJson["geometricSegmentations"][name] = info

        dumped_index_JSON: str = json.dumps(indexJson, ensure_ascii=False, indent=4)
        zip_file.writestr(CVSX_INDEX_JSON_FILENAME, data=dumped_index_JSON)

    # print(indexJson)
    zip_data = file.getvalue()

    with open(str(out_path.resolve()), "wb") as f:
        f.write(zip_data)

def _write_to_file(responses: list[QueryResponse], out_path: Path, format: OutputFormatsEnum):
    file = io.BytesIO()

    indexJson: CVSXFilesIndex = {
        "metadata": None,
        "query": None,
    }
    assets_folder_name = 'assets'
    match format:
        case OutputFormatsEnum.cvsx:
            _write_cvsx_to_file(file=file, responses=responses, indexJson=indexJson, out_path=out_path)
        case OutputFormatsEnum.mvsx:
            _write_mvsx_to_file(file=file, responses=responses, indexJson=indexJson, out_path=out_path, assets_folder_name=assets_folder_name)
        case _:
            raise Exception(f'Format {format} is not supported.')

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
    parsed_params = _parse_json_params(parsed_args.json_params_path)

    entry_id = parsed_params.entry_id
    source_db = parsed_params.source_db

    db = FileSystemVolumeServerDB(folder=Path(parsed_args.db_path))

    # initialize server
    volume_server = VolumeServerService(db)

    # 3. query metadata
    metadata = await volume_server.get_metadata(
        req=MetadataRequest(
            source=parsed_params.source_db, structure_id=parsed_params.entry_id
        )
    )
    grid_metadata: Metadata = metadata["grid"]
    annotations = metadata["annotation"]

    queries_list: list[QueryTaskBase] = []
    channel_ids = _get_channel_ids_from_metadata(grid_metadata)
    if "channel_id" in parsed_params:
        channel_ids = [parsed_params["channel_id"]]

    max_points = DEFAULT_MAX_POINTS
    timeframes = _get_volume_timeframes_from_metadata(grid_metadata)
    if "max_points" in parsed_params:
        max_points = parsed_params["max_points"]

    # TODO: set all timeframes to this
    # for segmentations as well
    if "time" in parsed_params:
        timeframes = [parsed_params["time"]]
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
            "segmentation_lattices", parsed_params, grid_metadata, volume_server
        )
    if (
        grid_metadata["segmentation_meshes"]
        and len(grid_metadata["segmentation_meshes"]["segmentation_ids"]) > 0
    ):
        mesh = _query_segmentation_data(
            "segmentation_meshes", parsed_params, grid_metadata, volume_server
        )
    if (
        grid_metadata["geometric_segmentation"]
        and len(grid_metadata["geometric_segmentation"]["segmentation_ids"]) > 0
    ):
        gs = _query_segmentation_data(
            "geometric_segmentation", parsed_params, grid_metadata, volume_server
        )

    queries_list = queries_list + lat + mesh + gs

    # NOTE: afterwards, do:
    responses: list[QueryResponse] = []
    responses.append(
        QueryResponse(response=grid_metadata, type="metadata", input_data={})
    )
    responses.append(
        QueryResponse(response=annotations, type="annotations", input_data={})
    )
    responses.append(QueryResponse(response=parsed_params, type="query", input_data={}))

    for query in queries_list:
        r = await query.execute()
        responses.append(r)

    _write_to_file(responses, parsed_args.out, parsed_args.format)


async def main():
    # add one required argument - json
    # drop support for simple queries at all
    main_parser = argparse.ArgumentParser(add_help=True)

    # common_subparsers = main_parser.add_subparsers(title='Query type', dest='query_type', help='Select one of: ')
    # COMMON ARGUMENTS
    # TODO: check if extension and format are in agreement (better) or exclude extension (worse)
    required_named = main_parser.add_argument_group("Required named arguments")
    # TODO: check if choices should be a list instead
    required_named.add_argument("--format", type=str, default='mvsx', choices=['mvsx', 'cvsx'], required=True, help="Produce CVSX or mvsx file as an output")
    required_named.add_argument("--db_path", type=str, required=True, help="Path to db")
    required_named.add_argument(
        "--out", type=str, required=True, help="Path to output file including extension"
    )
    required_named.add_argument(
        "--json_params_path",
        required=True,
        type=str,
        help="Path to .json file with query parameters",
    )

    args = main_parser.parse_args()

    await query(args)


if __name__ == "__main__":
    asyncio.run(main())
