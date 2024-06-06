"use strict";
/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
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
exports.SourceChoice = exports.actionToggleSegment = exports.actionSelectSegment = exports.findNodesByRef = exports.findNodesByTags = exports._actionShowSegments = exports.actionShowSegments = exports.actionToggleAllFilteredSegments = exports.parseCVSXJSON = void 0;
const volume_1 = require("molstar/lib/mol-model/volume");
const transforms_1 = require("molstar/lib/mol-plugin-state/transforms");
const state_1 = require("molstar/lib/mol-plugin/behavior/static/state");
const assets_1 = require("molstar/lib/mol-util/assets");
const param_choice_1 = require("molstar/lib/mol-util/param-choice");
const entry_segmentation_1 = require("./volumes-and-segmentations/entry-segmentation");
const utils_1 = require("./volumes-and-segmentations/volseg-api/utils");
function parseCVSXJSON(rawFile, plugin) {
    return __awaiter(this, void 0, void 0, function* () {
        const [fn, filedata] = rawFile;
        const file = new File([filedata], fn);
        const f = assets_1.Asset.File(file);
        const asset = plugin.managers.asset.resolve(f, 'string');
        const runnedAsset = (yield asset.run()).data;
        const parsedData = JSON.parse(runnedAsset);
        return parsedData;
    });
}
exports.parseCVSXJSON = parseCVSXJSON;
function actionToggleAllFilteredSegments(model, segmentationId, kind, filteredDescriptions) {
    return __awaiter(this, void 0, void 0, function* () {
        const current = model.currentState.value.visibleSegments.map(seg => seg.segmentKey);
        const currentForThisSegmentation = current.filter(c => (0, utils_1.parseSegmentKey)(c).segmentationId === segmentationId &&
            (0, utils_1.parseSegmentKey)(c).kind === kind);
        const currentForOtherSegmentations = current.filter(item => currentForThisSegmentation.indexOf(item) < 0);
        const allFilteredSegmentKeys = filteredDescriptions.map(d => {
            if (d.target_kind !== 'entry') {
                return (0, utils_1.createSegmentKey)(d.target_id.segment_id, d.target_id.segmentation_id, d.target_kind);
            }
        }).filter(Boolean);
        if (currentForThisSegmentation.length !== filteredDescriptions.length) {
            const allSegmentKeys = [...allFilteredSegmentKeys, ...currentForOtherSegmentations];
            yield actionShowSegments(allSegmentKeys, model);
        }
        else {
            yield actionShowSegments(currentForOtherSegmentations, model);
        }
    });
}
exports.actionToggleAllFilteredSegments = actionToggleAllFilteredSegments;
function actionShowSegments(segmentKeys, model) {
    return __awaiter(this, void 0, void 0, function* () {
        const allExistingLatticeSegmentationIds = model.metadata.value.raw.grid.segmentation_lattices.segmentation_ids;
        const allExistingMeshSegmentationIds = model.metadata.value.raw.grid.segmentation_meshes.segmentation_ids;
        const allExistingGeometricSegmentationIds = model.metadata.value.raw.grid.geometric_segmentation.segmentation_ids;
        if (segmentKeys.length === 0) {
            for (const id of allExistingLatticeSegmentationIds) {
                yield showSegments([], id, 'lattice', model);
            }
            for (const id of allExistingMeshSegmentationIds) {
                yield showSegments([], id, 'mesh', model);
            }
            for (const id of allExistingGeometricSegmentationIds) {
                yield showSegments([], id, 'primitive', model);
            }
        }
        const parsedSegmentKeys = segmentKeys.map(k => (0, utils_1.parseSegmentKey)(k));
        // LATTICES PART
        _actionShowSegments(parsedSegmentKeys, allExistingLatticeSegmentationIds, 'lattice', model);
        // MESHES PART
        _actionShowSegments(parsedSegmentKeys, allExistingMeshSegmentationIds, 'mesh', model);
        // GEOMETRIC SEGMENTATION PART
        _actionShowSegments(parsedSegmentKeys, allExistingGeometricSegmentationIds, 'primitive', model);
        yield model.updateStateNode({ visibleSegments: segmentKeys.map(s => ({ segmentKey: s })) });
    });
}
exports.actionShowSegments = actionShowSegments;
function _actionShowSegments(parsedSegmentKeys, existingSegmentationIds, kind, model) {
    return __awaiter(this, void 0, void 0, function* () {
        const segmentKeys = parsedSegmentKeys.filter(k => k.kind === kind);
        const SegmentationIdsToSegmentIds = new Map;
        for (const key of segmentKeys) {
            if (!SegmentationIdsToSegmentIds.has(key.segmentationId)) {
                SegmentationIdsToSegmentIds.set(key.segmentationId, [key.segmentId]);
            }
            else {
                // have this key, add segmentId
                const currentSegmentationIds = SegmentationIdsToSegmentIds.get(key.segmentationId);
                SegmentationIdsToSegmentIds.set(key.segmentationId, [...currentSegmentationIds, key.segmentId]);
            }
        }
        for (const id of existingSegmentationIds) {
            if (!SegmentationIdsToSegmentIds.has(id)) {
                SegmentationIdsToSegmentIds.set(id, []);
            }
        }
        const promises = [];
        SegmentationIdsToSegmentIds.forEach((value, key) => {
            promises.push(showSegments(value, key, kind, model));
        });
        yield Promise.all(promises);
    });
}
exports._actionShowSegments = _actionShowSegments;
function findNodesByTags(plugin, ...tags) {
    return plugin.state.data.selectQ(q => {
        let builder = q.root.subtree();
        for (const tag of tags)
            builder = builder.withTag(tag);
        return builder;
    });
}
exports.findNodesByTags = findNodesByTags;
function findNodesByRef(plugin, ref) {
    return plugin.state.data.selectQ(q => q.byRef(ref).subtree())[0];
}
exports.findNodesByRef = findNodesByRef;
function selectSegment(model, segmentId, segmentationId) {
    return __awaiter(this, void 0, void 0, function* () {
        if (segmentId === undefined || segmentId < 0 || !segmentationId)
            return;
        const segmentLoci = makeLoci([segmentId], segmentationId, model);
        if (!segmentLoci)
            return;
        model.plugin.managers.interactivity.lociSelects.select(segmentLoci, false);
    });
}
function makeLoci(segments, segmentationId, model) {
    var _a;
    const vis = findNodesByTags(model.plugin, entry_segmentation_1.SEGMENT_VISUAL_TAG, segmentationId)[0];
    if (!vis)
        return undefined;
    const repr = (_a = vis.obj) === null || _a === void 0 ? void 0 : _a.data.repr;
    const wholeLoci = repr.getAllLoci()[0];
    if (!wholeLoci || !volume_1.Volume.Segment.isLoci(wholeLoci))
        return undefined;
    return { loci: volume_1.Volume.Segment.Loci(wholeLoci.volume, segments), repr: repr };
}
function showSegments(segmentIds, segmentationId, kind, model) {
    return __awaiter(this, void 0, void 0, function* () {
        var _a, _b, _c, _d, _e;
        if (kind === 'lattice') {
            const repr = findNodesByTags(model.plugin, entry_segmentation_1.SEGMENT_VISUAL_TAG, segmentationId)[0];
            if (!repr)
                return;
            const selectedSegmentKey = model.currentState.value.selectedSegment;
            const parsedSelectedSegmentKey = (0, utils_1.parseSegmentKey)(selectedSegmentKey);
            const selectedSegmentId = parsedSelectedSegmentKey.segmentId;
            const selectedSegmentSegmentationId = parsedSelectedSegmentKey.segmentationId;
            const mustReselect = segmentIds.includes(selectedSegmentId) && !((_a = repr.params) === null || _a === void 0 ? void 0 : _a.values.type.params.segments.includes(selectedSegmentId));
            const update = model.plugin.build().toRoot();
            update.to(repr).update(transforms_1.StateTransforms.Representation.VolumeRepresentation3D, p => { p.type.params.segments = segmentIds; });
            yield update.commit();
            if (mustReselect) {
                yield selectSegment(model, selectedSegmentId, selectedSegmentSegmentationId);
            }
        }
        else if (kind === 'mesh') {
            const segmentsToShow = new Set(segmentIds);
            const visuals = findNodesByTags(model.plugin, 'mesh-segment-visual', segmentationId);
            for (const visual of visuals) {
                const theTag = (_c = (_b = visual.obj) === null || _b === void 0 ? void 0 : _b.tags) === null || _c === void 0 ? void 0 : _c.find(tag => tag.startsWith('segment-'));
                if (!theTag)
                    continue;
                const id = parseInt(theTag.split('-')[1]);
                const visibility = segmentsToShow.has(id);
                (0, state_1.setSubtreeVisibility)(model.plugin.state.data, visual.transform.ref, !visibility); // true means hide, ¯\_(ツ)_/¯
                segmentsToShow.delete(id);
            }
        }
        else if (kind === 'primitive') {
            const segmentsToShow = new Set(segmentIds);
            // This will select all segments of that segmentation
            const visuals = findNodesByTags(model.plugin, 'geometric-segmentation-visual', segmentationId);
            for (const visual of visuals) {
                const theTag = (_e = (_d = visual.obj) === null || _d === void 0 ? void 0 : _d.tags) === null || _e === void 0 ? void 0 : _e.find(tag => tag.startsWith('segment-'));
                if (!theTag)
                    continue;
                const id = parseInt(theTag.split('-')[1]);
                const visibility = segmentsToShow.has(id);
                (0, state_1.setSubtreeVisibility)(model.plugin.state.data, visual.transform.ref, !visibility); // true means hide, ¯\_(ツ)_/¯
                segmentsToShow.delete(id);
            }
        }
        else {
            throw new Error('Not supported');
        }
    });
}
function actionSelectSegment(model, segmentKey) {
    return __awaiter(this, void 0, void 0, function* () {
        if (segmentKey !== undefined && model.currentState.value.visibleSegments.find(s => s.segmentKey === segmentKey) === undefined) {
            // first make the segment visible if it is not
            yield actionToggleSegment(model, segmentKey);
        }
        yield model.updateStateNode({ selectedSegment: segmentKey });
    });
}
exports.actionSelectSegment = actionSelectSegment;
function actionToggleSegment(model, segmentKey) {
    return __awaiter(this, void 0, void 0, function* () {
        const current = model.currentState.value.visibleSegments.map(seg => seg.segmentKey);
        if (current.includes(segmentKey)) {
            yield actionShowSegments(current.filter(s => s !== segmentKey), model);
        }
        else {
            yield actionShowSegments([...current, segmentKey], model);
        }
    });
}
exports.actionToggleSegment = actionToggleSegment;
exports.SourceChoice = new param_choice_1.Choice({ emdb: 'EMDB', empiar: 'EMPIAR', idr: 'IDR', pdbe: 'PDBe', custom: 'CUSTOM' }, 'emdb');
