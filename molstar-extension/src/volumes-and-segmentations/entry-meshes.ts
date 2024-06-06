/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Adam Midlik <midlik@gmail.com>
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */

import { PluginStateObject } from '../../../mol-plugin-state/objects';
import { CreateGroup } from '../../../mol-plugin-state/transforms/misc';
import { ShapeRepresentation3D } from '../../../mol-plugin-state/transforms/representation';
import { setSubtreeVisibility } from '../../../mol-plugin/behavior/static/state';
import { PluginCommands } from '../../../mol-plugin/commands';
import { Color } from '../../../mol-util/color';
import { ColorNames } from '../../../mol-util/color/names';
import { Box3D } from '../../../mol-math/geometry';

// import { BACKGROUND_SEGMENT_VOLUME_THRESHOLD } from '../new-meshes/mesh-streaming/behavior';
import { BACKGROUND_OPACITY, BACKGROUND_SEGMENT_VOLUME_THRESHOLD, CreateMeshlistStateObject, FOREROUND_OPACITY, MeshShapeTransformer, MeshlistData, VolsegMeshSegmentation, meshSegmentParamsValues } from '../meshes/mesh-extension';
import { VolsegEntryData } from './entry-root';


import { StateObjectSelector } from '../../../mol-state';
import { ProjectMeshSegmentationDataParamsValues } from './transformers';

export const DEFAULT_MESH_DETAIL: number | null = 5; // null means worst

export class VolsegMeshSegmentationData {
    private entryData: VolsegEntryData;

    constructor(rootData: VolsegEntryData) {
        this.entryData = rootData;
    }

    async loadSegmentation() {
        // const hasMeshes = this.entryData.metadata.value!.meshSegmentIds.length > 0;
        // if (hasMeshes) {
        //     await this.showSegments(this.entryData.metadata.value!.allSegmentIds);
        // }
    }

    updateOpacity(opacity: number, segmentationId: string) {

        const visuals = this.entryData.findNodesByTags('mesh-segment-visual', segmentationId);
        const update = this.entryData.newUpdate();
        for (const visual of visuals) {
            update.to(visual).update(ShapeRepresentation3D, p => { (p as any).alpha = opacity; });
        }
        return update.commit();
    }

    async createMeshRepresentation3D(meshNode: StateObjectSelector<VolsegMeshSegmentation>, params: ProjectMeshSegmentationDataParamsValues) {
        const meshData = meshNode.data!.meshData;
        const ownerId = this.entryData.ref;
        const totalVolume = this.entryData.metadata.value!.gridTotalVolume;
        const segmentationId = params.segmentationId;
        for (const meshDataItem of meshData) {
            const update = this.entryData.plugin.build().to(meshNode);
            const meshListStateObj = await update.to(meshNode)
                .apply(CreateMeshlistStateObject,
                    {
                        segmentId: meshDataItem.meshSegmentParams.id,
                        ownerId: ownerId,
                        segmentationId: segmentationId
                    }
                )
                .commit();

            const transparentIfBboxAbove = BACKGROUND_SEGMENT_VOLUME_THRESHOLD * totalVolume;

            let transparent = false;
            if (transparentIfBboxAbove !== undefined && meshListStateObj.data) {
                const bbox = MeshlistData.bbox(meshListStateObj.data) || Box3D.zero();
                transparent = Box3D.volume(bbox) > transparentIfBboxAbove;
            }

            await this.entryData.plugin.build().to(meshListStateObj)
                .apply(MeshShapeTransformer, { color: meshDataItem.meshSegmentParams.color },)
                .apply(ShapeRepresentation3D,
                    { alpha: transparent ? BACKGROUND_OPACITY : FOREROUND_OPACITY },
                    { tags: ['mesh-segment-visual', `segment-${meshDataItem.meshSegmentParams.id}`, segmentationId] }
                )
                .commit();
        }
    }

    getMeshSegmentParams(segmentationId: string, timeframeIndex: number) {
        const params: meshSegmentParamsValues[] = [];
        const segmentsToCreate = this.entryData.metadata.value!.getMeshSegmentIdsForSegmentationIdAndTimeframe(segmentationId, timeframeIndex);
        const segmentAnnotations = this.entryData.metadata.value!.getAllSegmentAnotationsForSegmentationAndTimeframe(
            segmentationId,
            'mesh',
            timeframeIndex
        );
        for (const seg of segmentsToCreate) {
            const colorData = segmentAnnotations.find(a => a.segment_id === seg)?.color;
            const color = colorData && colorData.length >= 3 ? Color.fromNormalizedArray(colorData, 0) : ColorNames.gray;
            const label = `${segmentationId} | Segment ${seg}`;

            const detail = this.entryData.metadata.value!.getSufficientMeshDetail(segmentationId, timeframeIndex, seg, DEFAULT_MESH_DETAIL);
            const segmentParams: meshSegmentParamsValues = {
                id: seg,
                label: label,
                // url: url,
                color: color,
                detail: detail
            };
            params.push(segmentParams);
        }

        return params;
    }

    async createMeshGroup() {
        let group = this.entryData.findNodesByTags('mesh-segmentation-group')[0]?.transform.ref;
        if (!group) {
            const newGroupNode = await this.entryData.newUpdate().apply(CreateGroup, { label: 'Segmentation', description: 'Mesh' }, { tags: ['mesh-segmentation-group'], state: { isCollapsed: true } }).commit();
            group = newGroupNode.ref;
        }
        return group;
    }

    async highlightSegment(segmentId: number, segmentationId: string) {
        const visuals = this.entryData.findNodesByTags('mesh-segment-visual', `segment-${segmentId}`, segmentationId);
        for (const visual of visuals) {
            await PluginCommands.Interactivity.Object.Highlight(this.entryData.plugin, { state: this.entryData.plugin.state.data, ref: visual.transform.ref });
        }
    }

    async selectSegment(segment?: number, segmentationId?: string) {
        if (segment === undefined || segment < 0 || segmentationId === undefined) return;
        const visuals = this.entryData.findNodesByTags('mesh-segment-visual', `segment-${segment}`, segmentationId);
        const reprNode: PluginStateObject.Shape.Representation3D | undefined = visuals[0]?.obj;
        if (!reprNode) return;
        const loci = reprNode.data.repr.getAllLoci()[0];
        if (!loci) return;
        this.entryData.plugin.managers.interactivity.lociSelects.select({ loci: loci, repr: reprNode.data.repr }, false);
    }

    /** Make visible the specified set of mesh segments */
    async showSegments(segmentIds: number[], segmentationId: string) {
        const segmentsToShow = new Set(segmentIds);

        const visuals = this.entryData.findNodesByTags('mesh-segment-visual', segmentationId);
        for (const visual of visuals) {
            const theTag = visual.obj?.tags?.find(tag => tag.startsWith('segment-'));
            if (!theTag) continue;
            const id = parseInt(theTag.split('-')[1]);
            const visibility = segmentsToShow.has(id);
            setSubtreeVisibility(this.entryData.plugin.state.data, visual.transform.ref, !visibility); // true means hide, ¯\_(ツ)_/¯
            segmentsToShow.delete(id);
        }
    }
}
