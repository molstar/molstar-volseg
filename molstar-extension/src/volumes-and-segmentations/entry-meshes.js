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
exports.VolsegMeshSegmentationData = exports.DEFAULT_MESH_DETAIL = void 0;
const misc_1 = require("molstar/lib/mol-plugin-state/transforms/misc");
const representation_1 = require("molstar/lib/mol-plugin-state/transforms/representation");
const state_1 = require("molstar/lib/mol-plugin/behavior/static/state");
const commands_1 = require("molstar/lib/mol-plugin/commands");
const color_1 = require("molstar/lib/mol-util/color");
const names_1 = require("molstar/lib/mol-util/color/names");
const geometry_1 = require("molstar/lib/mol-math/geometry");
// import { BACKGROUND_SEGMENT_VOLUME_THRESHOLD } from '../new-meshes/mesh-streaming/behavior';
const mesh_extension_1 = require("../meshes/mesh-extension");
exports.DEFAULT_MESH_DETAIL = 5; // null means worst
class VolsegMeshSegmentationData {
    constructor(rootData) {
        this.entryData = rootData;
    }
    loadSegmentation() {
        return __awaiter(this, void 0, void 0, function* () {
            // const hasMeshes = this.entryData.metadata.value!.meshSegmentIds.length > 0;
            // if (hasMeshes) {
            //     await this.showSegments(this.entryData.metadata.value!.allSegmentIds);
            // }
        });
    }
    updateOpacity(opacity, segmentationId) {
        const visuals = this.entryData.findNodesByTags('mesh-segment-visual', segmentationId);
        const update = this.entryData.newUpdate();
        for (const visual of visuals) {
            update.to(visual).update(representation_1.ShapeRepresentation3D, p => { p.alpha = opacity; });
        }
        return update.commit();
    }
    createMeshRepresentation3D(meshNode, params) {
        return __awaiter(this, void 0, void 0, function* () {
            const meshData = meshNode.data.meshData;
            const ownerId = this.entryData.ref;
            const totalVolume = this.entryData.metadata.value.gridTotalVolume;
            const segmentationId = params.segmentationId;
            for (const meshDataItem of meshData) {
                const update = this.entryData.plugin.build().to(meshNode);
                const meshListStateObj = yield update.to(meshNode)
                    .apply(mesh_extension_1.CreateMeshlistStateObject, {
                    segmentId: meshDataItem.meshSegmentParams.id,
                    ownerId: ownerId,
                    segmentationId: segmentationId
                })
                    .commit();
                const transparentIfBboxAbove = mesh_extension_1.BACKGROUND_SEGMENT_VOLUME_THRESHOLD * totalVolume;
                let transparent = false;
                if (transparentIfBboxAbove !== undefined && meshListStateObj.data) {
                    const bbox = mesh_extension_1.MeshlistData.bbox(meshListStateObj.data) || geometry_1.Box3D.zero();
                    transparent = geometry_1.Box3D.volume(bbox) > transparentIfBboxAbove;
                }
                yield this.entryData.plugin.build().to(meshListStateObj)
                    .apply(mesh_extension_1.MeshShapeTransformer, { color: meshDataItem.meshSegmentParams.color })
                    .apply(representation_1.ShapeRepresentation3D, { alpha: transparent ? mesh_extension_1.BACKGROUND_OPACITY : mesh_extension_1.FOREROUND_OPACITY }, { tags: ['mesh-segment-visual', `segment-${meshDataItem.meshSegmentParams.id}`, segmentationId] })
                    .commit();
            }
        });
    }
    getMeshSegmentParams(segmentationId, timeframeIndex) {
        var _a;
        const params = [];
        const segmentsToCreate = this.entryData.metadata.value.getMeshSegmentIdsForSegmentationIdAndTimeframe(segmentationId, timeframeIndex);
        const segmentAnnotations = this.entryData.metadata.value.getAllSegmentAnotationsForSegmentationAndTimeframe(segmentationId, 'mesh', timeframeIndex);
        for (const seg of segmentsToCreate) {
            const colorData = (_a = segmentAnnotations.find(a => a.segment_id === seg)) === null || _a === void 0 ? void 0 : _a.color;
            const color = colorData && colorData.length >= 3 ? color_1.Color.fromNormalizedArray(colorData, 0) : names_1.ColorNames.gray;
            const label = `${segmentationId} | Segment ${seg}`;
            const detail = this.entryData.metadata.value.getSufficientMeshDetail(segmentationId, timeframeIndex, seg, exports.DEFAULT_MESH_DETAIL);
            const segmentParams = {
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
    createMeshGroup() {
        return __awaiter(this, void 0, void 0, function* () {
            var _a;
            let group = (_a = this.entryData.findNodesByTags('mesh-segmentation-group')[0]) === null || _a === void 0 ? void 0 : _a.transform.ref;
            if (!group) {
                const newGroupNode = yield this.entryData.newUpdate().apply(misc_1.CreateGroup, { label: 'Segmentation', description: 'Mesh' }, { tags: ['mesh-segmentation-group'], state: { isCollapsed: true } }).commit();
                group = newGroupNode.ref;
            }
            return group;
        });
    }
    highlightSegment(segmentId, segmentationId) {
        return __awaiter(this, void 0, void 0, function* () {
            const visuals = this.entryData.findNodesByTags('mesh-segment-visual', `segment-${segmentId}`, segmentationId);
            for (const visual of visuals) {
                yield commands_1.PluginCommands.Interactivity.Object.Highlight(this.entryData.plugin, { state: this.entryData.plugin.state.data, ref: visual.transform.ref });
            }
        });
    }
    selectSegment(segment, segmentationId) {
        return __awaiter(this, void 0, void 0, function* () {
            var _a;
            if (segment === undefined || segment < 0 || segmentationId === undefined)
                return;
            const visuals = this.entryData.findNodesByTags('mesh-segment-visual', `segment-${segment}`, segmentationId);
            const reprNode = (_a = visuals[0]) === null || _a === void 0 ? void 0 : _a.obj;
            if (!reprNode)
                return;
            const loci = reprNode.data.repr.getAllLoci()[0];
            if (!loci)
                return;
            this.entryData.plugin.managers.interactivity.lociSelects.select({ loci: loci, repr: reprNode.data.repr }, false);
        });
    }
    /** Make visible the specified set of mesh segments */
    showSegments(segmentIds, segmentationId) {
        return __awaiter(this, void 0, void 0, function* () {
            var _a, _b;
            const segmentsToShow = new Set(segmentIds);
            const visuals = this.entryData.findNodesByTags('mesh-segment-visual', segmentationId);
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
}
exports.VolsegMeshSegmentationData = VolsegMeshSegmentationData;
