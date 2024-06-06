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
exports.VolsegGeometricSegmentationData = void 0;
const transforms_1 = require("molstar/lib/mol-plugin-state/transforms");
const misc_1 = require("molstar/lib/mol-plugin-state/transforms/misc");
const representation_1 = require("molstar/lib/mol-plugin-state/transforms/representation");
const state_1 = require("molstar/lib/mol-plugin/behavior/static/state");
const commands_1 = require("molstar/lib/mol-plugin/commands");
const shape_primitives_1 = require("./shape_primitives");
const GEOMETRIC_SEGMENTATION_GROUP_TAG = 'geometric-segmentation-group';
class VolsegGeometricSegmentationData {
    constructor(rootData) {
        this.entryData = rootData;
    }
    createGeometricSegmentationGroup() {
        return __awaiter(this, void 0, void 0, function* () {
            var _a;
            let group = (_a = this.entryData.findNodesByTags(GEOMETRIC_SEGMENTATION_GROUP_TAG)[0]) === null || _a === void 0 ? void 0 : _a.transform.ref;
            if (!group) {
                const newGroupNode = yield this.entryData.newUpdate().apply(misc_1.CreateGroup, { label: 'Segmentation', description: 'Geometric segmentation' }, { tags: [GEOMETRIC_SEGMENTATION_GROUP_TAG], state: { isCollapsed: true } }).commit();
                group = newGroupNode.ref;
            }
            return group;
        });
    }
    createGeometricSegmentationRepresentation3D(gsNode, params) {
        return __awaiter(this, void 0, void 0, function* () {
            const gsData = gsNode.cell.obj.data;
            const { timeframeIndex, segmentationId } = params;
            const descriptions = this.entryData.metadata.value.getDescriptions(segmentationId, 'primitive', timeframeIndex);
            const segmentAnnotations = this.entryData.metadata.value.getAllSegmentAnotationsForSegmentationAndTimeframe(segmentationId, 'primitive', timeframeIndex);
            const update = this.entryData.newUpdate().to(gsNode.ref);
            for (const primitiveData of gsData.shapePrimitiveData.shape_primitive_list) {
                const color = (0, shape_primitives_1._get_target_segment_color)(segmentAnnotations, primitiveData.id);
                const opacity = color[3];
                update
                    .apply(shape_primitives_1.CreateShapePrimitiveProvider, { segmentId: primitiveData.id, descriptions: descriptions, segmentAnnotations: segmentAnnotations, segmentationId: segmentationId })
                    .apply(transforms_1.StateTransforms.Representation.ShapeRepresentation3D, { alpha: opacity }, { tags: ['geometric-segmentation-visual', segmentationId, `segment-${primitiveData.id}`] });
            }
            yield update.commit();
        });
    }
    showSegments(segmentIds, segmentationId) {
        return __awaiter(this, void 0, void 0, function* () {
            var _a, _b;
            const segmentsToShow = new Set(segmentIds);
            // This will select all segments of that segmentation
            const visuals = this.entryData.findNodesByTags('geometric-segmentation-visual', segmentationId);
            for (const visual of visuals) {
                const theTag = (_b = (_a = visual.obj) === null || _a === void 0 ? void 0 : _a.tags) === null || _b === void 0 ? void 0 : _b.find(tag => tag.startsWith('segment-'));
                if (!theTag)
                    continue;
                const id = parseInt(theTag.split('-')[1]);
                const visibility = segmentsToShow.has(id);
                (0, state_1.setSubtreeVisibility)(this.entryData.plugin.state.data, visual.transform.ref, !visibility); // true means hide, ¯\_(ツ)_/¯
                segmentsToShow.delete(id);
            }
        });
    }
    highlightSegment(segmentId, segmentationId) {
        return __awaiter(this, void 0, void 0, function* () {
            const visuals = this.entryData.findNodesByTags('geometric-segmentation-visual', `segment-${segmentId}`, segmentationId);
            for (const visual of visuals) {
                yield commands_1.PluginCommands.Interactivity.Object.Highlight(this.entryData.plugin, { state: this.entryData.plugin.state.data, ref: visual.transform.ref });
            }
        });
    }
    updateOpacity(opacity, segmentationId) {
        const visuals = this.entryData.findNodesByTags('geometric-segmentation-visual', segmentationId);
        const update = this.entryData.newUpdate();
        for (const visual of visuals) {
            update.to(visual).update(representation_1.ShapeRepresentation3D, p => { p.alpha = opacity; });
        }
        return update.commit();
    }
    selectSegment(segment, segmentationId) {
        return __awaiter(this, void 0, void 0, function* () {
            var _a;
            if (segment === undefined || segment < 0 || segmentationId === undefined)
                return;
            const visuals = this.entryData.findNodesByTags('geometric-segmentation-visual', `segment-${segment}`, segmentationId);
            const reprNode = (_a = visuals[0]) === null || _a === void 0 ? void 0 : _a.obj;
            if (!reprNode)
                return;
            const loci = reprNode.data.repr.getAllLoci()[0];
            if (!loci)
                return;
            this.entryData.plugin.managers.interactivity.lociSelects.select({ loci: loci, repr: reprNode.data.repr }, false);
        });
    }
}
exports.VolsegGeometricSegmentationData = VolsegGeometricSegmentationData;
