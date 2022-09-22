import json
from collections import defaultdict

from math import ceil
from typing import Optional, Union

from db.interface.i_preprocessed_db import IReadOnlyPreprocessedDb
from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from .i_volume_server import IVolumeServer
from .preprocessed_volume_to_cif.i_volume_to_cif_converter import IVolumeToCifConverter
from volume_server.src.requests.volume_request.i_volume_request import IVolumeRequest
from volume_server.src.requests.request_box import RequestBox, calc_request_box
from .requests.cell_request.i_cell_request import ICellRequest
from .requests.entries_request.i_entries_request import IEntriesRequest
from .requests.mesh_request.i_mesh_request import IMeshRequest
from .requests.metadata_request.i_metadata_request import IMetadataRequest

from volume_server.src.requests.volume import VolumeRequestInfo, VolumeRequestBox

__MAX_DOWN_SAMPLING_VALUE__ = 1000000


class VolumeServerV1(IVolumeServer):
    async def _filter_entries_by_keyword(self, namespace: str, entries: list[str], keyword: str):
        filtered = []
        for entry in entries:
            if keyword in entry:
                filtered.append(entry)
                continue

            annotations = await self.db.read_annotations(namespace, entry)
            if keyword.lower() in json.dumps(annotations).lower():
                filtered.append(entry)
                continue

        return filtered

    async def get_entries(self, req: IEntriesRequest) -> dict:
        limit = req.limit()
        entries = dict()
        if limit == 0:
            return entries

        sources = await self.db.list_sources()
        for source in sources:
            retrieved = await self.db.list_entries(source, limit)
            if req.keyword():
                retrieved = await self._filter_entries_by_keyword(source, retrieved, req.keyword())

            if len(retrieved) == 0:
                continue

            entries[source] = retrieved
            limit -= len(retrieved)
            if limit == 0:
                break

        return entries

    async def get_metadata(self, req: IMetadataRequest) -> Union[bytes, str]:
        grid = await self.db.read_metadata(req.source(), req.structure_id())
        try:
            annotation = await self.db.read_annotations(req.source(), req.structure_id())
        except Exception as e:
            annotation = None

        # converted = self.volume_to_cif.convert_metadata(grid_metadata)
        return {"grid": grid.json_metadata(), "annotation": annotation}

    def __init__(self, db: IReadOnlyPreprocessedDb, volume_to_cif: IVolumeToCifConverter):
        self.db = db
        self.volume_to_cif = volume_to_cif

    async def read_box(self, *, req: Union[IVolumeRequest, ICellRequest], metadata: IPreprocessedMetadata, lattice_id: int, box: RequestBox) -> bytes:
        print(f"Request Box")
        print(f"  Downsampling: {box.downsampling_rate}")
        print(f"  Bottom Left: {box.bottom_left}")
        print(f"  Top Right: {box.top_right}")
        print(f"  Volume: {box.volume}")

        with self.db.read(namespace=req.source(), key=req.structure_id()) as reader:
            db_slice = await reader.read_slice(
                lattice_id=lattice_id,
                down_sampling_ratio=box.downsampling_rate,
                box=(box.bottom_left, box.top_right),
            )

        cif = self.volume_to_cif.convert(db_slice, metadata, box)
        return cif

    async def get_cell(self, req: ICellRequest) -> bytes:
        metadata = await self.db.read_metadata(req.source(), req.structure_id())
        lattice_id = self.decide_lattice(req, metadata)
        box = self.decide_cell_downsampling(req, metadata)
                
        return await self.read_box(
            req=req,
            metadata=metadata,
            lattice_id=lattice_id,
            box=box,
        )

    async def read_box(self, *, req: Union[IVolumeRequest, ICellRequest], metadata: IPreprocessedMetadata, lattice_id: int, box: RequestBox) -> bytes:
        print(f"Request Box")
        print(f"  Downsampling: {box.downsampling_rate}")
        print(f"  Bottom Left: {box.bottom_left}")
        print(f"  Top Right: {box.top_right}")
        print(f"  Volume: {box.volume}")

        with self.db.read(namespace=req.source(), key=req.structure_id()) as reader:
            db_slice = await reader.read_slice(
                lattice_id=lattice_id,
                down_sampling_ratio=box.downsampling_rate,
                box=(box.bottom_left, box.top_right),
            )

        cif = self.volume_to_cif.convert(db_slice, metadata, box)
        return cif

    async def get_volume_data(self, req: VolumeRequestInfo, req_box: Optional[VolumeRequestBox] = None) -> bytes:
        metadata = await self.db.read_metadata(req.source, req.structure_id)
        
        lattice_ids = metadata.segmentation_lattice_ids() or []
        if req.segmentation_id not in lattice_ids:
            lattice_id = lattice_ids[0] if len(lattice_ids) > 0 else None
        else:
            lattice_id = req.segmentation_id

        slice_box = self._decide_slice_box(req, req_box, metadata)

        if slice_box is None:
            # TODO: return empty result instead of exception?
            raise RuntimeError("No data for request box")

        print(f"Request Box")
        print(f"  Downsampling: {slice_box.downsampling_rate}")
        print(f"  Bottom Left: {slice_box.bottom_left}")
        print(f"  Top Right: {slice_box.top_right}")
        print(f"  Volume: {slice_box.volume}")

        with self.db.read(namespace=req.source, key=req.structure_id) as reader:
            if req.data_kind == "all":
                db_slice = await reader.read_slice(
                    lattice_id=lattice_id,
                    down_sampling_ratio=slice_box.downsampling_rate,
                    box=(slice_box.bottom_left, slice_box.top_right),
                )
            elif req.data_kind == "volume":
                db_slice = await reader.read_volume_slice(
                    down_sampling_ratio=slice_box.downsampling_rate,
                    box=(slice_box.bottom_left, slice_box.top_right),
                ) 
            elif req.data_kind == "segmentation":
                db_slice = await reader.read_segmentation_slice(
                    lattice_id=lattice_id,
                    down_sampling_ratio=slice_box.downsampling_rate,
                    box=(slice_box.bottom_left, slice_box.top_right),
                )
            else:
                # This should be validated on the Pydantic data model level, but one never knows...
                raise RuntimeError(f"{req.data_kind} is not a valid request data kind")

        return self.volume_to_cif.convert(db_slice, metadata, slice_box)


    async def get_volume(self, req: IVolumeRequest) -> bytes:  # TODO: add binary cif to the project
        metadata = await self.db.read_metadata(req.source(), req.structure_id())
        lattice_id = self.decide_lattice(req, metadata)
        box = self.decide_downsampling(req, metadata)

        if box is None:
            # TODO: return empty result instead of exception?
            raise RuntimeError("No data for request box")
        
        return await self.read_box(
            req=req,
            metadata=metadata,
            lattice_id=lattice_id,
            box=box,
        )

    async def get_meshes(self, req: IMeshRequest) -> list[object]:
        with self.db.read(req.source(), req.id()) as context:
            try:
                meshes = await context.read_meshes(req.segment_id(), req.detail_lvl())
            except KeyError as e:
                print("Exception in get_meshes: " + str(e))
                meta = await self.db.read_metadata(req.source(), req.id())
                segments_levels = self._extract_segments_detail_levels(meta)
                error_msg = f'Invalid segment_id={req.segment_id()} or detail_lvl={req.detail_lvl()} (available segment_ids and detail_lvls: {segments_levels})'
                raise error_msg

        return meshes
        # cif = self.volume_to_cif.convert_meshes(meshes, metadata, req.detail_lvl(), [10, 10, 10])  # TODO: replace 10,10,10 with cell size

    def _extract_segments_detail_levels(self, meta: IPreprocessedMetadata) -> dict[int, list[int]]:
        '''Extract available segment_ids and detail_lvls for each segment_id'''
        meta_js = meta.json_metadata()
        segments_levels = meta_js.get('segmentation_meshes', {}).get('mesh_component_numbers', {}).get('segment_ids',
                                                                                                       {})
        result: dict[int, list[int]] = defaultdict(list)
        for seg, obj in segments_levels.items():
            for lvl in obj.get('detail_lvls', {}).keys():
                result[int(seg)].append(int(lvl))
        sorted_result = {seg: sorted(result[seg]) for seg in sorted(result.keys())}
        return sorted_result

    def decide_lattice(self, req: Union[ICellRequest, IVolumeRequest], metadata: IPreprocessedMetadata) -> Optional[int]:
        ids = metadata.segmentation_lattice_ids() or []
        if req.segmentation_id() not in ids:
            return ids[0] if len(ids) > 0 else None
        return req.segmentation_id()

    def _decide_slice_box(self, req: VolumeRequestInfo, req_box: Optional[VolumeRequestBox], metadata: IPreprocessedMetadata) -> Optional[RequestBox]:
        box = None
        max_points = req.max_points

        for downsampling_rate in sorted(metadata.volume_downsamplings()):
            if req_box:
                box = calc_request_box(req_box.bottom_left, req_box.top_right, metadata, downsampling_rate) 
            else:
                box = RequestBox(
                    downsampling_rate=downsampling_rate,
                    bottom_left=(0, 0, 0),
                    top_right=tuple(d - 1 for d in metadata.sampled_grid_dimensions(downsampling_rate))
                )

            # TODO: decide what to do when max_points is 0
            # e.g. whether to return the lowest downsampling or highest
            if box.volume < max_points:
                return box

        return box

    def decide_downsampling(self, req: IVolumeRequest, metadata: IPreprocessedMetadata) -> Optional[RequestBox]:
        box = None
        max_points = req.max_points()

        req_min = (req.x_min(), req.y_min(), req.z_min())
        req_max = (req.x_max(), req.y_max(), req.z_max())

        for downsampling_rate in sorted(metadata.volume_downsamplings()):
            box = calc_request_box(req_min, req_max, metadata, downsampling_rate)
            if box is None:
                return None
            # TODO: decide what to do when max_points is 0
            # e.g. whether to return the lowest downsampling or highest
            if box.volume < max_points:
                return box

        return box

    def decide_cell_downsampling(self, req: ICellRequest, metadata: IPreprocessedMetadata) -> RequestBox:
        max_points = req.max_points()

        for downsampling_rate in sorted(metadata.volume_downsamplings()):
            box = RequestBox(
                downsampling_rate=downsampling_rate,
                bottom_left=(0, 0, 0),
                top_right=tuple(d - 1 for d in metadata.sampled_grid_dimensions(downsampling_rate))
            )
            # TODO: decide what to do when max_points is 0
            if box.volume < max_points:
                return box

        return box
