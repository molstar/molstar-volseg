import json
from collections import defaultdict
from math import ceil, floor
from typing import Optional, Tuple, Union

from db.protocol import VolumeServerDB
from db.models import VolumeMetadata

from app.api.requests import (
    EntriesRequest,
    MeshRequest,
    MetadataRequest,
    VolumeRequestBox,
    VolumeRequestDataKind,
    VolumeRequestInfo,
)
from app.core.models import GridSliceBox
from app.serialization.cif import serialize_volume_slice

__MAX_DOWN_SAMPLING_VALUE__ = 1000000


class VolumeServerService:
    def __init__(self, db: VolumeServerDB):
        self.db = db

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

    async def get_entries(self, req: EntriesRequest) -> dict:
        limit = req.limit
        entries = dict()
        if limit == 0:
            return entries

        sources = await self.db.list_sources()
        for source in sources:
            retrieved = await self.db.list_entries(source, limit)
            if req.keyword:
                retrieved = await self._filter_entries_by_keyword(source, retrieved, req.keyword)

            if len(retrieved) == 0:
                continue

            entries[source] = retrieved
            limit -= len(retrieved)
            if limit == 0:
                break

        return entries

    async def get_metadata(self, req: MetadataRequest) -> Union[bytes, str]:
        grid = await self.db.read_metadata(req.source, req.structure_id)
        try:
            annotation = await self.db.read_annotations(req.source, req.structure_id)
        except Exception:
            annotation = None

        return {"grid": grid.json_metadata(), "annotation": annotation}

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
            if req.data_kind == VolumeRequestDataKind.all:
                db_slice = await reader.read_slice(
                    lattice_id=lattice_id,
                    down_sampling_ratio=slice_box.downsampling_rate,
                    box=(slice_box.bottom_left, slice_box.top_right),
                )
            elif req.data_kind == VolumeRequestDataKind.volume:
                db_slice = await reader.read_volume_slice(
                    down_sampling_ratio=slice_box.downsampling_rate,
                    box=(slice_box.bottom_left, slice_box.top_right),
                )
            elif req.data_kind == VolumeRequestDataKind.segmentation:
                db_slice = await reader.read_segmentation_slice(
                    lattice_id=lattice_id,
                    down_sampling_ratio=slice_box.downsampling_rate,
                    box=(slice_box.bottom_left, slice_box.top_right),
                )
            else:
                # This should be validated on the Pydantic data model level, but one never knows...
                raise RuntimeError(f"{req.data_kind} is not a valid request data kind")

        return serialize_volume_slice(db_slice, metadata, slice_box)

    async def get_meshes(self, req: MeshRequest) -> list[object]:
        with self.db.read(req.source, req.structure_id) as context:
            try:
                meshes = await context.read_meshes(req.segment_id, req.detail_lvl)
            except KeyError as e:
                print("Exception in get_meshes: " + str(e))
                meta = await self.db.read_metadata(req.source, req.structure_id)
                segments_levels = self._extract_segments_detail_levels(meta)
                error_msg = f"Invalid segment_id={req.segment_id} or detail_lvl={req.detail_lvl} (available segment_ids and detail_lvls: {segments_levels})"
                raise error_msg

        return meshes
        # cif = convert_meshes(meshes, metadata, req.detail_lvl(), [10, 10, 10])  # TODO: replace 10,10,10 with cell size

    def _extract_segments_detail_levels(self, meta: VolumeMetadata) -> dict[int, list[int]]:
        """Extract available segment_ids and detail_lvls for each segment_id"""
        meta_js = meta.json_metadata()
        segments_levels = (
            meta_js.get("segmentation_meshes", {}).get("mesh_component_numbers", {}).get("segment_ids", {})
        )
        result: dict[int, list[int]] = defaultdict(list)
        for seg, obj in segments_levels.items():
            for lvl in obj.get("detail_lvls", {}).keys():
                result[int(seg)].append(int(lvl))
        sorted_result = {seg: sorted(result[seg]) for seg in sorted(result.keys())}
        return sorted_result

    def _decide_slice_box(
        self, req: VolumeRequestInfo, req_box: Optional[VolumeRequestBox], metadata: VolumeMetadata
    ) -> Optional[GridSliceBox]:
        box = None
        max_points = req.max_points

        for downsampling_rate in sorted(metadata.volume_downsamplings()):
            if req_box:
                box = calc_slice_box(req_box.bottom_left, req_box.top_right, metadata, downsampling_rate)
            else:
                box = GridSliceBox(
                    downsampling_rate=downsampling_rate,
                    bottom_left=(0, 0, 0),
                    top_right=tuple(d - 1 for d in metadata.sampled_grid_dimensions(downsampling_rate)),
                )

            # TODO: decide what to do when max_points is 0
            # e.g. whether to return the lowest downsampling or highest
            if box.volume < max_points:
                return box

        return box


def calc_slice_box(
    req_min: Tuple[float, float, float],
    req_max: Tuple[float, float, float],
    meta: VolumeMetadata,
    downsampling_rate: int,
) -> Optional[GridSliceBox]:
    origin, voxel_size, grid_dimensions = (
        meta.origin(),
        meta.voxel_size(downsampling_rate),
        meta.sampled_grid_dimensions(downsampling_rate),
    )

    bottom_left = tuple(max(0, floor((req_min[i] - origin[i]) / voxel_size[i])) for i in range(3))
    top_right = tuple(min(grid_dimensions[i] - 1, ceil((req_max[i] - origin[i]) / voxel_size[i])) for i in range(3))

    # Check if the box is outside the available data
    if any(bottom_left[i] >= grid_dimensions[i] for i in range(3)) or any(top_right[i] < 0 for i in range(3)):
        return None

    return GridSliceBox(downsampling_rate=downsampling_rate, bottom_left=bottom_left, top_right=top_right)
