import json
from collections import defaultdict
from math import ceil, floor
from typing import Optional, Tuple

from cellstar_db.models import (
    DownsamplingLevelInfo,
    GeometricSegmentationData,
    MeshesData,
    VolumeMetadata,
)
from cellstar_db.protocol import VolumeServerDB
from cellstar_query.core.models import GridSliceBox
from cellstar_query.core.timing import Timing
from cellstar_query.requests import (
    EntriesRequest,
    GeometricSegmentationRequest,
    MeshRequest,
    MetadataRequest,
    VolumeRequestBox,
    VolumeRequestDataKind,
    VolumeRequestInfo,
)
from cellstar_query.serialization.cif import (
    serialize_meshes,
    serialize_volume_info,
    serialize_volume_slice,
)

__MAX_DOWN_SAMPLING_VALUE__ = 1000000


class VolumeServerService:
    def __init__(self, db: VolumeServerDB):
        self.db = db

    async def _filter_entries_by_keyword(
        self, namespace: str, entries: list[str], keyword: str
    ) -> list[str]:
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

    async def get_entries(self, req: EntriesRequest) -> dict[str, list[str]]:
        limit = req.limit
        entries: dict[str, list[str]] = {}
        if limit == 0:
            return entries

        sources = await self.db.list_sources()
        for source in sources:
            retrieved = await self.db.list_entries(source, limit)
            if req.keyword:
                retrieved = await self._filter_entries_by_keyword(
                    source, retrieved, req.keyword
                )

            if len(retrieved) == 0:
                continue

            entries[source] = retrieved
            limit -= len(retrieved)
            if limit == 0:
                break

        return entries

    async def get_metadata(self, req: MetadataRequest) -> dict:
        grid = await self.db.read_metadata(req.source, req.structure_id)
        try:
            annotation = await self.db.read_annotations(req.source, req.structure_id)
        except Exception:
            annotation = None

        return {"grid": grid.model_dump(), "annotation": annotation}

    async def get_volume_data(
        self, req: VolumeRequestInfo, req_box: Optional[VolumeRequestBox] = None
    ) -> bytes:
        metadata = await self.db.read_metadata(req.source, req.structure_id)

        lattice_ids = metadata.segmentation_lattice_ids() or []
        if req.segmentation_id not in lattice_ids:
            lattice_id = lattice_ids[0] if len(lattice_ids) > 0 else None
        else:
            lattice_id = req.segmentation_id

        slice_box = self._decide_slice_box(req.max_points, req_box, metadata)

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
                    channel_id=req.channel_id,
                    time=req.time,
                )
            elif req.data_kind == VolumeRequestDataKind.volume:
                db_slice = await reader.read_volume_slice(
                    down_sampling_ratio=slice_box.downsampling_rate,
                    box=(slice_box.bottom_left, slice_box.top_right),
                    channel_id=req.channel_id,
                    time=req.time,
                )
            elif req.data_kind == VolumeRequestDataKind.segmentation:
                db_slice = await reader.read_segmentation_slice(
                    lattice_id=lattice_id,
                    down_sampling_ratio=slice_box.downsampling_rate,
                    box=(slice_box.bottom_left, slice_box.top_right),
                    time=req.time,
                )
            else:
                # This should be validated on the Pydantic data model level, but one never knows...
                raise RuntimeError(f"{req.data_kind} is not a valid request data kind")

        return serialize_volume_slice(db_slice, metadata, slice_box)

    async def get_volume_info(self, req: MetadataRequest) -> bytes:
        metadata = await self.db.read_metadata(req.source, req.structure_id)
        box = self._decide_slice_box(None, None, metadata)
        return serialize_volume_info(metadata, box)

    async def get_geometric_segmentation(
        self, req: GeometricSegmentationRequest
    ) -> GeometricSegmentationData:
        with self.db.read(req.source, req.structure_id) as context:
            try:
                gs = await context.read_geometric_segmentation(
                    segmentation_id=req.segmentation_id, time=req.time
                )
                # TODO: fix "error": "local variable 'gs' referenced before assignment"
            except Exception as e:
                raise Exception("Exception in get_geometric_segmentation: " + str(e))
        return gs

    async def get_meshes_bcif(self, req: MeshRequest) -> bytes:
        with Timing("read metadata"):
            metadata = await self.db.read_metadata(req.source, req.structure_id)
        # with Timing("decide box"):
        #     box = self._decide_slice_box(None, None, metadata)
        # for meshes instead can create box
        # for original resolution
        box = GridSliceBox(
            downsampling_rate=1,
            bottom_left=(0, 0, 0),
            top_right=tuple(d - 1 for d in metadata.sampled_grid_dimensions(1)),  # type: ignore  # length is 3
        )
        with Timing("read meshes"):
            with self.db.read(req.source, req.structure_id) as context:
                try:
                    meshes = await context.read_meshes(
                        segmentation_id=req.segmentation_id,
                        time=req.time,
                        segment_id=req.segment_id,
                        detail_lvl=req.detail_lvl,
                    )
                    # try:  # DEBUG, TODO REMOVE
                    #     meshes1 = await context.read_meshes(req.segment_id+1, req.detail_lvl)
                    #     for mesh in meshes1: mesh['mesh_id'] = 1
                    #     meshes += meshes1
                    #     meshes2 = await context.read_meshes(req.segment_id+2, req.detail_lvl)
                    #     for mesh in meshes2: mesh['mesh_id'] = 2
                    #     meshes += meshes2
                    # except KeyError:
                    #     pass
                except KeyError as e:
                    print("Exception in get_meshes: " + str(e))
                    meta = await self.db.read_metadata(req.source, req.structure_id)
                    segments_levels = self._extract_segments_detail_levels(
                        meta, timeframe=req.time, segmentation_id=req.segmentation_id
                    )
                    error_msg = f"Invalid segment_id={req.segment_id} or detail_lvl={req.detail_lvl} (available segment_ids and detail_lvls: {segments_levels})"
                    raise KeyError(error_msg)
        with Timing("serialize meshes"):
            bcif = serialize_meshes(meshes, metadata, box, req.time)

        return bcif

    async def get_meshes(self, req: MeshRequest) -> MeshesData:
        with self.db.read(req.source, req.structure_id) as context:
            try:
                meshes = await context.read_meshes(
                    segmentation_id=req.segmentation_id,
                    time=req.time,
                    segment_id=req.segment_id,
                    detail_lvl=req.detail_lvl,
                )
            except KeyError as e:
                print("Exception in get_meshes: " + str(e))
                meta = await self.db.read_metadata(req.source, req.structure_id)
                segments_levels = self._extract_segments_detail_levels(
                    meta, timeframe=req.time, segmentation_id=req.segmentation_id
                )
                error_msg = f"Invalid segment_id={req.segment_id} or detail_lvl={req.detail_lvl} (available segment_ids and detail_lvls: {segments_levels})"
                raise KeyError(error_msg)

        return meshes
        # cif = convert_meshes(meshes, metadata, req.detail_lvl(), [10, 10, 10])  # TODO: replace 10,10,10 with cell size

    def _check_if_downsampling_exists_in_segmentations(
        self, level: int, metadata: VolumeMetadata
    ):
        # for each lattice available check, if at least in some it is missing, return false
        for lattice_id in metadata.segmentation_lattice_ids():
            segm_downsamplings: list[DownsamplingLevelInfo] = (
                metadata.segmentation_downsamplings(lattice_id)
            )
            # check if downsampling exists
            exists = any(i["level"] == level for i in segm_downsamplings)
            # check if
            if not exists:
                return False
            right_downsampling: DownsamplingLevelInfo = list(
                filter(lambda i: i["level"] == level, segm_downsamplings)
            )[0]
            if right_downsampling["available"] == False:
                return False

        return True

    def _extract_segments_detail_levels(
        self, meta: VolumeMetadata, timeframe: int, segmentation_id: str
    ) -> dict[int, list[int]]:
        """Extract available segment_ids and detail_lvls for each segment_id"""
        meta_js = meta.model_dump()
        # should accept timeframe parameter and segmentation id

        segments_levels = (
            meta_js.get("segmentation_meshes", {})
            .get("segmentation_metadata", {})
            .get(segmentation_id, {})
            .get("mesh_timeframes", {})
            .get(str(timeframe), {})
            .get("segment_ids", {})
        )
        result: dict[int, list[int]] = defaultdict(list)
        for seg, obj in segments_levels.items():
            for lvl in obj.get("detail_lvls", {}).keys():
                result[int(seg)].append(int(lvl))
        sorted_result = {seg: sorted(result[seg]) for seg in sorted(result.keys())}
        return sorted_result

    def _decide_slice_box(
        self,
        max_points: Optional[int],
        req_box: Optional[VolumeRequestBox],
        metadata: VolumeMetadata,
    ) -> Optional[GridSliceBox]:
        """`max_points=None` means unlimited number of points"""
        box = None

        # how it works
        # loop over all downsampling levels
        # even if not available, it should decide original slice box for meshes
        # loops over downsampling rates
        # 1, 2, 4, 8
        # on each iteration checks request box
        # if provided - calculates box based on that
        # if not, calculates box based on downsampling
        # returns first box
        for downsampling_level_info in metadata.volume_downsamplings():
            if downsampling_level_info["available"] == False:
                continue

            if len(metadata.segmentation_lattice_ids()) > 0:
                level = downsampling_level_info["level"]
                exists = self._check_if_downsampling_exists_in_segmentations(
                    level, metadata
                )
                if not exists:
                    continue

            downsampling_rate = downsampling_level_info["level"]
            if req_box:
                box = calc_slice_box(
                    req_box.bottom_left, req_box.top_right, metadata, downsampling_rate
                )
            # for cell query
            # this branch works
            else:
                box = GridSliceBox(
                    downsampling_rate=downsampling_rate,
                    bottom_left=(0, 0, 0),
                    top_right=tuple(d - 1 for d in metadata.sampled_grid_dimensions(downsampling_rate)),  # type: ignore  # length is 3
                )

            # TODO: decide what to do when max_points is 0
            # e.g. whether to return the lowest downsampling or highest

            # returns first downsampling if max_points is None
            # of if box volume is lower than max_points

            # so it loops over all downsamplings
            # and tries to find the one satisfying the the max points
            #
            if max_points is None or (box is not None and box.volume < max_points):
                return box

        return box


def calc_slice_box(
    req_min: Tuple[float, float, float],
    req_max: Tuple[float, float, float],
    meta: VolumeMetadata,
    downsampling_rate: int,
) -> Optional[GridSliceBox]:
    origin, voxel_size, grid_dimensions = (
        meta.origin(downsampling_rate),
        meta.voxel_size(downsampling_rate),
        meta.sampled_grid_dimensions(downsampling_rate),
    )

    bottom_left: tuple[int, int, int] = tuple(max(0, floor((req_min[i] - origin[i]) / voxel_size[i])) for i in range(3))  # type: ignore  # length is 3
    top_right: tuple[int, int, int] = tuple(min(grid_dimensions[i] - 1, ceil((req_max[i] - origin[i]) / voxel_size[i])) for i in range(3))  # type: ignore  # length is 3

    # Check if the box is outside the available data
    if any(bottom_left[i] >= grid_dimensions[i] for i in range(3)) or any(
        top_right[i] < 0 for i in range(3)
    ):
        return None

    return GridSliceBox(
        downsampling_rate=downsampling_rate,
        bottom_left=bottom_left,
        top_right=top_right,
    )
