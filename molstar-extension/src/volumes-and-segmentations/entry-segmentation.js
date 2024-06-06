"use strict";
/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Adam Midlik <midlik@gmail.com>
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.VolsegLatticeSegmentationData = exports.SEGMENT_VISUAL_TAG = void 0;
const volume_1 = require("molstar/lib/mol-model/volume");
const volume_representation_params_1 = require("molstar/lib/mol-plugin-state/helpers/volume-representation-params");
const transforms_1 = require("molstar/lib/mol-plugin-state/transforms");
const misc_1 = require("molstar/lib/mol-plugin-state/transforms/misc");
const commands_1 = require("molstar/lib/mol-plugin/commands");
const color_1 = require("molstar/lib/mol-util/color");
const global_state_1 = require("./global-state");
const utils_1 = require("./volseg-api/utils");
const GROUP_TAG = 'lattice-segmentation-group';
exports.SEGMENT_VISUAL_TAG = 'lattice-segment-visual';
const DEFAULT_SEGMENT_COLOR = color_1.Color.fromNormalizedRgb(0.8, 0.8, 0.8);
class VolsegLatticeSegmentationData {
    constructor(rootData) {
        this.entryData = rootData;
    }
    createSegmentationGroup() {
        return __awaiter(this, void 0, void 0, function* () {
            var _a;
            this.createColorMap();
            let group = (_a = this.entryData.findNodesByTags(GROUP_TAG)[0]) === null || _a === void 0 ? void 0 : _a.transform.ref;
            if (!group) {
                const newGroupNode = yield this.entryData.newUpdate().apply(misc_1.CreateGroup, { label: 'Segmentation', description: 'Lattice' }, { tags: [GROUP_TAG], state: { isCollapsed: true } }).commit();
                group = newGroupNode.ref;
            }
            return group;
        });
    }
    createSegmentationRepresentation3D(segmentationNode, params) {
        return __awaiter(this, void 0, void 0, function* () {
            var _a, _b;
            const segmentationData = segmentationNode.data;
            const segmentationId = params.segmentationId;
            const segmentation = volume_1.Volume.Segmentation.get(segmentationData);
            const segmentIds = Array.from((_a = segmentation === null || segmentation === void 0 ? void 0 : segmentation.segments.keys()) !== null && _a !== void 0 ? _a : []);
            yield this.entryData.newUpdate().to(segmentationNode)
                .apply(transforms_1.StateTransforms.Representation.VolumeRepresentation3D, (0, volume_representation_params_1.createVolumeRepresentationParams)(this.entryData.plugin, segmentationData, {
                type: 'segment',
                typeParams: { tryUseGpu: (_b = global_state_1.VolsegGlobalStateData.getGlobalState(this.entryData.plugin)) === null || _b === void 0 ? void 0 : _b.tryUseGpu },
                color: 'volume-segment',
                colorParams: { palette: this.getPaletteForSegmentation(segmentationId, segmentIds) },
            }), { tags: [exports.SEGMENT_VISUAL_TAG, segmentationId] }).commit();
        });
    }
    // creates colors for lattice segments
    getPaletteForSegmentation(segmentationId, segmentIds) {
        const colorMapForSegmentation = this.colorMap.get(segmentationId);
        if (!colorMapForSegmentation) {
            const colors = segmentIds.map(segid => DEFAULT_SEGMENT_COLOR);
            return { name: 'colors', params: { list: { kind: 'set', colors: colors } } };
        }
        else {
            const colors = segmentIds.map(segid => { var _a; return (_a = colorMapForSegmentation.get(segid)) !== null && _a !== void 0 ? _a : DEFAULT_SEGMENT_COLOR; });
            return { name: 'colors', params: { list: { kind: 'set', colors: colors } } };
        }
    }
    createColorMap() {
        const colorMapForAllSegmentations = new Map();
        if (this.entryData.metadata.value.allAnnotations) {
            for (const annotation of this.entryData.metadata.value.allAnnotations) {
                if (annotation.color) {
                    const color = color_1.Color.fromNormalizedArray(annotation.color, 0);
                    if (colorMapForAllSegmentations.get(annotation.segmentation_id)) {
                        // segmentation id exists
                        // there is a map inside with at least one segment
                        const colorMapForSegmentation = colorMapForAllSegmentations.get(annotation.segmentation_id);
                        colorMapForSegmentation.set(annotation.segment_id, color);
                        colorMapForAllSegmentations.set(annotation.segmentation_id, colorMapForSegmentation);
                    }
                    else {
                        // does not exist, create
                        const colorMapForSegmentation = new Map();
                        colorMapForSegmentation.set(annotation.segment_id, color);
                        colorMapForAllSegmentations.set(annotation.segmentation_id, colorMapForSegmentation);
                    }
                    this.colorMap = colorMapForAllSegmentations;
                }
            }
        }
    }
    updateOpacity(opacity, segmentationId) {
        return __awaiter(this, void 0, void 0, function* () {
            const s = this.entryData.findNodesByTags(exports.SEGMENT_VISUAL_TAG, segmentationId)[0];
            const update = this.entryData.newUpdate();
            update.to(s).update(transforms_1.StateTransforms.Representation.VolumeRepresentation3D, p => { p.type.params.alpha = opacity; });
            return yield update.commit();
        });
    }
    makeLoci(segments, segmentationId) {
        var _a;
        const vis = this.entryData.findNodesByTags(exports.SEGMENT_VISUAL_TAG, segmentationId)[0];
        if (!vis)
            return undefined;
        const repr = (_a = vis.obj) === null || _a === void 0 ? void 0 : _a.data.repr;
        const wholeLoci = repr.getAllLoci()[0];
        if (!wholeLoci || !volume_1.Volume.Segment.isLoci(wholeLoci))
            return undefined;
        return { loci: volume_1.Volume.Segment.Loci(wholeLoci.volume, segments), repr: repr };
    }
    highlightSegment(segmentId, segmentationId) {
        return __awaiter(this, void 0, void 0, function* () {
            const segmentLoci = this.makeLoci([segmentId], segmentationId);
            if (!segmentLoci)
                return;
            this.entryData.plugin.managers.interactivity.lociHighlights.highlight(segmentLoci, false);
        });
    }
    selectSegment(segmentId, segmentationId) {
        return __awaiter(this, void 0, void 0, function* () {
            if (segmentId === undefined || segmentId < 0 || !segmentationId)
                return;
            const segmentLoci = this.makeLoci([segmentId], segmentationId);
            if (!segmentLoci)
                return;
            this.entryData.plugin.managers.interactivity.lociSelects.select(segmentLoci, false);
        });
    }
    /** Make visible the specified set of lattice segments */
    showSegments(segmentIds, segmentationId) {
        return __awaiter(this, void 0, void 0, function* () {
            var _a;
            const repr = this.entryData.findNodesByTags(exports.SEGMENT_VISUAL_TAG, segmentationId)[0];
            if (!repr)
                return;
            const selectedSegmentKey = this.entryData.currentState.value.selectedSegment;
            const parsedSelectedSegmentKey = (0, utils_1.parseSegmentKey)(selectedSegmentKey);
            const selectedSegmentId = parsedSelectedSegmentKey.segmentId;
            const selectedSegmentSegmentationId = parsedSelectedSegmentKey.segmentationId;
            const mustReselect = segmentIds.includes(selectedSegmentId) && !((_a = repr.params) === null || _a === void 0 ? void 0 : _a.values.type.params.segments.includes(selectedSegmentId));
            const update = this.entryData.newUpdate();
            update.to(repr).update(transforms_1.StateTransforms.Representation.VolumeRepresentation3D, p => { p.type.params.segments = segmentIds; });
            yield update.commit();
            if (mustReselect) {
                yield this.selectSegment(selectedSegmentId, selectedSegmentSegmentationId);
            }
        });
    }
    setTryUseGpu(tryUseGpu) {
        return __awaiter(this, void 0, void 0, function* () {
            const visuals = this.entryData.findNodesByTags(exports.SEGMENT_VISUAL_TAG);
            for (const visual of visuals) {
                const oldParams = visual.transform.params;
                if (oldParams.type.params.tryUseGpu === !tryUseGpu) {
                    const newParams = Object.assign(Object.assign({}, oldParams), { type: Object.assign(Object.assign({}, oldParams.type), { params: Object.assign(Object.assign({}, oldParams.type.params), { tryUseGpu: tryUseGpu }) }) });
                    const update = this.entryData.newUpdate().to(visual.transform.ref).update(newParams);
                    yield commands_1.PluginCommands.State.Update(this.entryData.plugin, { state: this.entryData.plugin.state.data, tree: update, options: { doNotUpdateCurrent: true } });
                }
            }
        });
    }
}
exports.VolsegLatticeSegmentationData = VolsegLatticeSegmentationData;
