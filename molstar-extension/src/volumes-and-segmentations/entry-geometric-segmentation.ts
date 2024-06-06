/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Adam Midlik <midlik@gmail.com>
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */

import { PluginStateObject } from '../../../mol-plugin-state/objects';
import { StateTransforms } from '../../../mol-plugin-state/transforms';
import { CreateGroup } from '../../../mol-plugin-state/transforms/misc';
import { ShapeRepresentation3D } from '../../../mol-plugin-state/transforms/representation';
import { setSubtreeVisibility } from '../../../mol-plugin/behavior/static/state';
import { PluginCommands } from '../../../mol-plugin/commands';
import { StateObjectSelector } from '../../../mol-state';
import { VolsegEntryData } from './entry-root';
import { CreateShapePrimitiveProvider, VolsegGeometricSegmentation, VolsegShapePrimitivesData, _get_target_segment_color } from './shape_primitives';
import { ProjectGeometricSegmentationDataParamsValues } from './transformers';


const GEOMETRIC_SEGMENTATION_GROUP_TAG = 'geometric-segmentation-group';

export class VolsegGeometricSegmentationData {
    private entryData: VolsegEntryData;

    constructor(rootData: VolsegEntryData) {
        this.entryData = rootData;
    }

    async createGeometricSegmentationGroup() {
        let group = this.entryData.findNodesByTags(GEOMETRIC_SEGMENTATION_GROUP_TAG)[0]?.transform.ref;
        if (!group) {
            const newGroupNode = await this.entryData.newUpdate().apply(CreateGroup,
                { label: 'Segmentation', description: 'Geometric segmentation' }, { tags: [GEOMETRIC_SEGMENTATION_GROUP_TAG], state: { isCollapsed: true } }).commit();
            group = newGroupNode.ref;
        }
        return group;
    }

    async createGeometricSegmentationRepresentation3D(gsNode: StateObjectSelector<VolsegGeometricSegmentation>, params: ProjectGeometricSegmentationDataParamsValues) {
        const gsData: VolsegShapePrimitivesData = gsNode.cell!.obj!.data;
        const { timeframeIndex, segmentationId } = params;
        const descriptions = this.entryData.metadata.value!.getDescriptions(segmentationId, 'primitive', timeframeIndex);
        const segmentAnnotations = this.entryData.metadata.value!.getAllSegmentAnotationsForSegmentationAndTimeframe(segmentationId, 'primitive', timeframeIndex);
        const update = this.entryData.newUpdate().to(gsNode.ref);
        for (const primitiveData of gsData.shapePrimitiveData.shape_primitive_list) {
            const color = _get_target_segment_color(segmentAnnotations, primitiveData.id);
            const opacity = color[3];
            update
                .apply(CreateShapePrimitiveProvider, { segmentId: primitiveData.id, descriptions: descriptions, segmentAnnotations: segmentAnnotations, segmentationId: segmentationId })
                .apply(StateTransforms.Representation.ShapeRepresentation3D, { alpha: opacity }, { tags: ['geometric-segmentation-visual', segmentationId, `segment-${primitiveData.id}`] });
        }
        await update.commit();
    }


    async showSegments(segmentIds: number[], segmentationId: string) {
        const segmentsToShow = new Set(segmentIds);

        // This will select all segments of that segmentation
        const visuals = this.entryData.findNodesByTags('geometric-segmentation-visual', segmentationId);
        for (const visual of visuals) {
            const theTag = visual.obj?.tags?.find(tag => tag.startsWith('segment-'));
            if (!theTag) continue;
            const id = parseInt(theTag.split('-')[1]);
            const visibility = segmentsToShow.has(id);
            setSubtreeVisibility(this.entryData.plugin.state.data, visual.transform.ref, !visibility); // true means hide, ¯\_(ツ)_/¯
            segmentsToShow.delete(id);
        }
    }

    async highlightSegment(segmentId: number, segmentationId: string) {
        const visuals = this.entryData.findNodesByTags('geometric-segmentation-visual', `segment-${segmentId}`, segmentationId);
        for (const visual of visuals) {
            await PluginCommands.Interactivity.Object.Highlight(this.entryData.plugin, { state: this.entryData.plugin.state.data, ref: visual.transform.ref });
        }
    }

    updateOpacity(opacity: number, segmentationId: string) {
        const visuals = this.entryData.findNodesByTags('geometric-segmentation-visual', segmentationId);
        const update = this.entryData.newUpdate();
        for (const visual of visuals) {
            update.to(visual).update(ShapeRepresentation3D, p => { (p as any).alpha = opacity; });
        }
        return update.commit();
    }

    async selectSegment(segment?: number, segmentationId?: string) {
        if (segment === undefined || segment < 0 || segmentationId === undefined) return;
        const visuals = this.entryData.findNodesByTags('geometric-segmentation-visual', `segment-${segment}`, segmentationId);
        const reprNode: PluginStateObject.Shape.Representation3D | undefined = visuals[0]?.obj;
        if (!reprNode) return;
        const loci = reprNode.data.repr.getAllLoci()[0];
        if (!loci) return;
        this.entryData.plugin.managers.interactivity.lociSelects.select({ loci: loci, repr: reprNode.data.repr }, false);
    }
}