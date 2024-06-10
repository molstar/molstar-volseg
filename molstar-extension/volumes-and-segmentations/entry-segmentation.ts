/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Adam Midlik <midlik@gmail.com>
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */

import { Volume } from 'molstar/lib/mol-model/volume';
import { createVolumeRepresentationParams } from 'molstar/lib/mol-plugin-state/helpers/volume-representation-params';
import { StateTransforms } from 'molstar/lib/mol-plugin-state/transforms';
import { CreateGroup } from 'molstar/lib/mol-plugin-state/transforms/misc';
import { PluginCommands } from 'molstar/lib/mol-plugin/commands';
import { Color } from 'molstar/lib/mol-util/color';

import { VolsegEntryData } from './entry-root';
import { VolumeVisualParams } from './entry-volume';
import { VolsegGlobalStateData } from './global-state';
import { StateObjectSelector } from 'molstar/lib/mol-state';
import { PluginStateObject } from 'molstar/lib/mol-plugin-state/objects';
import { ProjectLatticeSegmentationDataParamsValues } from './transformers';
import { parseSegmentKey } from './volseg-api/utils';


const GROUP_TAG = 'lattice-segmentation-group';
export const SEGMENT_VISUAL_TAG = 'lattice-segment-visual';

const DEFAULT_SEGMENT_COLOR = Color.fromNormalizedRgb(0.8, 0.8, 0.8);


export class VolsegLatticeSegmentationData {
    private entryData: VolsegEntryData;
    // should map segmentation Id to Map<number, Color>
    private colorMap: Map<string, Map<number, Color>> = new Map();

    constructor(rootData: VolsegEntryData) {
        this.entryData = rootData;
    }

    async createSegmentationGroup() {
        this.createColorMap();
        let group = this.entryData.findNodesByTags(GROUP_TAG)[0]?.transform.ref;
        if (!group) {
            const newGroupNode = await this.entryData.newUpdate().apply(CreateGroup,
                { label: 'Segmentation', description: 'Lattice' }, { tags: [GROUP_TAG], state: { isCollapsed: true } }).commit();
            group = newGroupNode.ref;
        }
        return group;
    }

    async createSegmentationRepresentation3D(segmentationNode: StateObjectSelector<PluginStateObject.Volume.Data>, params: ProjectLatticeSegmentationDataParamsValues) {
        const segmentationData = segmentationNode.data as Volume;
        const segmentationId = params.segmentationId;
        const segmentation = Volume.Segmentation.get(segmentationData);
        const segmentIds: number[] = Array.from(segmentation?.segments.keys() ?? []);
        await this.entryData.newUpdate().to(segmentationNode)
            .apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.entryData.plugin, segmentationData, {
                type: 'segment',
                typeParams: { tryUseGpu: VolsegGlobalStateData.getGlobalState(this.entryData.plugin)?.tryUseGpu },
                color: 'volume-segment',
                colorParams: { palette: this.getPaletteForSegmentation(segmentationId, segmentIds) },
            }), { tags: [SEGMENT_VISUAL_TAG, segmentationId] }).commit();
    }

    // creates colors for lattice segments

    private getPaletteForSegmentation(segmentationId: string, segmentIds: number[]) {
        const colorMapForSegmentation = this.colorMap.get(segmentationId);
        if (!colorMapForSegmentation) {
            const colors = segmentIds.map(segid => DEFAULT_SEGMENT_COLOR);
            return { name: 'colors' as const, params: { list: { kind: 'set' as const, colors: colors } } };
        } else {
            const colors = segmentIds.map(segid => colorMapForSegmentation.get(segid) ?? DEFAULT_SEGMENT_COLOR);
            return { name: 'colors' as const, params: { list: { kind: 'set' as const, colors: colors } } };
        }
    }

    private createColorMap() {
        const colorMapForAllSegmentations = new Map<string, any>();
        if (this.entryData.metadata.value!.allAnnotations) {
            for (const annotation of this.entryData.metadata.value!.allAnnotations) {
                if (annotation.color) {
                    const color = Color.fromNormalizedArray(annotation.color, 0);
                    if (colorMapForAllSegmentations.get(annotation.segmentation_id)) {
                        // segmentation id exists
                        // there is a map inside with at least one segment
                        const colorMapForSegmentation: Map<number, Color> = colorMapForAllSegmentations.get(annotation.segmentation_id);
                        colorMapForSegmentation.set(annotation.segment_id, color);
                        colorMapForAllSegmentations.set(annotation.segmentation_id, colorMapForSegmentation);
                    } else {
                        // does not exist, create
                        const colorMapForSegmentation = new Map<number, Color>();
                        colorMapForSegmentation.set(annotation.segment_id, color);
                        colorMapForAllSegmentations.set(annotation.segmentation_id, colorMapForSegmentation);
                    }
                    this.colorMap = colorMapForAllSegmentations;
                }
            }
        }
    }

    async updateOpacity(opacity: number, segmentationId: string) {
        const s = this.entryData.findNodesByTags(SEGMENT_VISUAL_TAG, segmentationId)[0];
        const update = this.entryData.newUpdate();
        update.to(s).update(StateTransforms.Representation.VolumeRepresentation3D, p => { p.type.params.alpha = opacity; });
        return await update.commit();
    }
    private makeLoci(segments: number[], segmentationId: string) {
        const vis = this.entryData.findNodesByTags(SEGMENT_VISUAL_TAG, segmentationId)[0];
        if (!vis) return undefined;
        const repr = vis.obj?.data.repr;
        const wholeLoci = repr.getAllLoci()[0];
        if (!wholeLoci || !Volume.Segment.isLoci(wholeLoci)) return undefined;
        return { loci: Volume.Segment.Loci(wholeLoci.volume, segments), repr: repr };
    }
    async highlightSegment(segmentId: number, segmentationId: string) {
        const segmentLoci = this.makeLoci([segmentId], segmentationId);
        if (!segmentLoci) return;
        this.entryData.plugin.managers.interactivity.lociHighlights.highlight(segmentLoci, false);
    }
    async selectSegment(segmentId?: number, segmentationId?: string) {
        if (segmentId === undefined || segmentId < 0 || !segmentationId) return;
        const segmentLoci = this.makeLoci([segmentId], segmentationId);
        if (!segmentLoci) return;
        this.entryData.plugin.managers.interactivity.lociSelects.select(segmentLoci, false);
    }

    /** Make visible the specified set of lattice segments */
    async showSegments(segmentIds: number[], segmentationId: string) {
        const repr = this.entryData.findNodesByTags(SEGMENT_VISUAL_TAG, segmentationId)[0];
        if (!repr) return;
        const selectedSegmentKey = this.entryData.currentState.value.selectedSegment;
        const parsedSelectedSegmentKey = parseSegmentKey(selectedSegmentKey);
        const selectedSegmentId = parsedSelectedSegmentKey.segmentId;
        const selectedSegmentSegmentationId = parsedSelectedSegmentKey.segmentationId;
        const mustReselect = segmentIds.includes(selectedSegmentId) && !repr.params?.values.type.params.segments.includes(selectedSegmentId);
        const update = this.entryData.newUpdate();
        update.to(repr).update(StateTransforms.Representation.VolumeRepresentation3D, p => { p.type.params.segments = segmentIds; });
        await update.commit();
        if (mustReselect) {
            await this.selectSegment(selectedSegmentId, selectedSegmentSegmentationId);
        }
    }

    async setTryUseGpu(tryUseGpu: boolean) {
        const visuals = this.entryData.findNodesByTags(SEGMENT_VISUAL_TAG);
        for (const visual of visuals) {
            const oldParams: VolumeVisualParams = visual.transform.params;
            if (oldParams.type.params.tryUseGpu === !tryUseGpu) {
                const newParams = { ...oldParams, type: { ...oldParams.type, params: { ...oldParams.type.params, tryUseGpu: tryUseGpu } } };
                const update = this.entryData.newUpdate().to(visual.transform.ref).update(newParams);
                await PluginCommands.State.Update(this.entryData.plugin, { state: this.entryData.plugin.state.data, tree: update, options: { doNotUpdateCurrent: true } });
            }
        }
    }
}