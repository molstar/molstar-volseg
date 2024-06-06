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
exports.loadCVSXFromAnything = void 0;
const entry_root_1 = require("../volumes-and-segmentations/entry-root");
const transformers_1 = require("../volumes-and-segmentations/transformers");
const utils_1 = require("../volumes-and-segmentations/volseg-api/utils");
function loadCVSXFromAnything(plugin, data) {
    return __awaiter(this, void 0, void 0, function* () {
        var _a, _b, _c;
        yield plugin.build().to(data).apply(transformers_1.VolsegGlobalStateFromFile, {}, { state: { isGhost: true } }).commit();
        const entryNode = yield plugin.build().to(data).apply(transformers_1.VolsegEntryFromFile).commit();
        yield plugin.build().to(entryNode).apply(transformers_1.VolsegStateFromEntry, {}, { state: { isGhost: true } }).commit();
        if (entryNode.data) {
            // TODO: change - get from filesIndex, but from metadata is ok too
            // since query contains a single timeframe, or all
            const entryData = entryNode.data;
            let timeframeIndex = entryData.metadata.value.raw.grid.volumes.time_info.start;
            let channelIds = entryData.metadata.value.raw.grid.volumes.channel_ids;
            if (entryData.filesData.query.channel_id) {
                channelIds = [entryData.filesData.query.channel_id];
            }
            if (entryData.filesData.query.time) {
                timeframeIndex = entryData.filesData.query.time;
            }
            // always has Volumes
            const group = yield entryNode.data.volumeData.createVolumeGroup();
            const updatedChannelsData = [];
            const results = [];
            for (const channelId of channelIds) {
                const volumeParams = { timeframeIndex: timeframeIndex, channelId: channelId };
                const volumeNode = yield plugin.build().to(group).apply(transformers_1.ProjectVolumeData, volumeParams, { tags: [entry_root_1.VOLUME_NODE_TAG] }).commit();
                const result = yield entryNode.data.volumeData.createVolumeRepresentation3D(volumeNode, volumeParams);
                results.push(result);
            }
            for (const result of results) {
                if (result) {
                    const isovalue = result.isovalue.kind === 'relative' ? result.isovalue.relativeValue : result.isovalue.absoluteValue;
                    updatedChannelsData.push({
                        channelId: result.channelId, volumeIsovalueKind: result.isovalue.kind, volumeIsovalueValue: isovalue, volumeType: result.volumeType, volumeOpacity: result.opacity,
                        label: result.label,
                        color: result.color
                    });
                }
            }
            yield entryNode.data.updateStateNode({ channelsData: [...updatedChannelsData] });
            const hasLattices = (_a = entryData.filesData) === null || _a === void 0 ? void 0 : _a.latticeSegmentations;
            if (hasLattices) {
                // filter only lattices for timeframeIndex
                const latticesForTimeframeIndex = hasLattices.filter(l => l.timeframeIndex === timeframeIndex);
                const segmentationIds = latticesForTimeframeIndex.map(l => l.segmentationId);
                // loop over lattices and create one for each
                const group = yield entryNode.data.latticeSegmentationData.createSegmentationGroup();
                for (const segmentationId of segmentationIds) {
                    const descriptionsForLattice = entryNode.data.metadata.value.getDescriptions(segmentationId, 'lattice', timeframeIndex);
                    const segmentLabels = (0, utils_1.getSegmentLabelsFromDescriptions)(descriptionsForLattice);
                    const segmentationParams = {
                        timeframeIndex: timeframeIndex,
                        segmentationId: segmentationId,
                        segmentLabels: segmentLabels,
                        ownerId: entryNode.data.ref
                    };
                    const segmentationNode = yield plugin.build().to(group).apply(transformers_1.ProjectSegmentationData, segmentationParams, { tags: [entry_root_1.LATTICE_SEGMENTATION_NODE_TAG] }).commit();
                    yield entryNode.data.latticeSegmentationData.createSegmentationRepresentation3D(segmentationNode, segmentationParams);
                }
            }
            const hasGeometricSegmentation = (_b = entryData.filesData) === null || _b === void 0 ? void 0 : _b.geometricSegmentations;
            if (hasGeometricSegmentation) {
                const segmentationIds = hasGeometricSegmentation.map(g => g.segmentationId);
                const group = yield entryNode.data.geometricSegmentationData.createGeometricSegmentationGroup();
                for (const segmentationId of segmentationIds) {
                    const geometricSegmentationParams = {
                        segmentationId: segmentationId,
                        timeframeIndex: timeframeIndex
                    };
                    const geometricSegmentationNode = yield plugin.build().to(group).apply(transformers_1.ProjectGeometricSegmentationData, geometricSegmentationParams, { tags: [entry_root_1.GEOMETRIC_SEGMENTATION_NODE_TAG] }).commit();
                    yield entryNode.data.geometricSegmentationData.createGeometricSegmentationRepresentation3D(geometricSegmentationNode, geometricSegmentationParams);
                }
            }
            const hasMeshes = (_c = entryData.filesData) === null || _c === void 0 ? void 0 : _c.meshSegmentations;
            if (hasMeshes) {
                const segmentationIds = hasMeshes.map(m => m.segmentationId);
                const group = yield entryNode.data.meshSegmentationData.createMeshGroup();
                for (const segmentationId of segmentationIds) {
                    const meshSegmentParams = entryData.meshSegmentationData.getMeshSegmentParams(segmentationId, timeframeIndex);
                    const meshParams = {
                        meshSegmentParams: meshSegmentParams,
                        segmentationId: segmentationId,
                        timeframeIndex: timeframeIndex
                    };
                    const meshNode = yield plugin.build().to(group).apply(transformers_1.ProjectMeshData, meshParams, { tags: [entry_root_1.MESH_SEGMENTATION_NODE_TAG] }).commit();
                    yield entryNode.data.meshSegmentationData.createMeshRepresentation3D(meshNode, meshParams);
                }
            }
        }
        ;
        return entryNode;
    });
}
exports.loadCVSXFromAnything = loadCVSXFromAnything;
