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
var _a;
Object.defineProperty(exports, "__esModule", { value: true });
exports.LoadVolseg = exports.NewVolseg = exports.NewVolsegVolumeServerConfig = void 0;
const objects_1 = require("molstar/lib/mol-plugin-state/objects");
const behavior_1 = require("molstar/lib/mol-plugin/behavior");
const config_1 = require("molstar/lib/mol-plugin/config");
const mol_state_1 = require("molstar/lib/mol-state");
const mol_task_1 = require("molstar/lib/mol-task");
const api_1 = require("./volseg-api/api");
const entry_root_1 = require("./entry-root");
const global_state_1 = require("./global-state");
const helpers_1 = require("./helpers");
const transformers_1 = require("./transformers");
const ui_1 = require("./ui");
const utils_1 = require("./volseg-api/utils");
const common_1 = require("../common");
// TODO: temp change, put there 'localhost'
const DEBUGGING = typeof window !== 'undefined' ? ((_a = window === null || window === void 0 ? void 0 : window.location) === null || _a === void 0 ? void 0 : _a.hostname) === 'localhost' || '127.0.0.1' : false;
exports.NewVolsegVolumeServerConfig = {
    // DefaultServer: new PluginConfigItem('volseg-volume-server', DEFAULT_VOLUME_SERVER_V2),
    DefaultServer: new config_1.PluginConfigItem('volseg-volume-server', DEBUGGING ? 'http://localhost:9000/v1' : api_1.DEFAULT_VOLSEG_SERVER),
};
exports.NewVolseg = behavior_1.PluginBehavior.create({
    name: 'new-volseg',
    category: 'misc',
    display: {
        name: 'New Volseg',
        description: 'New Volseg'
    },
    ctor: class extends behavior_1.PluginBehavior.Handler {
        register() {
            this.ctx.state.data.actions.add(exports.LoadVolseg);
            this.ctx.customStructureControls.set('new-volseg', ui_1.VolsegUI);
            this.initializeEntryLists(); // do not await
            const entries = new Map();
            this.subscribeObservable(this.ctx.state.data.events.cell.created, o => {
                if (o.cell.obj instanceof entry_root_1.VolsegEntryData)
                    entries.set(o.ref, o.cell.obj);
            });
            this.subscribeObservable(this.ctx.state.data.events.cell.removed, o => {
                if (entries.has(o.ref)) {
                    entries.get(o.ref).dispose();
                    entries.delete(o.ref);
                }
            });
        }
        unregister() {
            this.ctx.state.data.actions.remove(exports.LoadVolseg);
            this.ctx.customStructureControls.delete('new-volseg');
        }
        initializeEntryLists() {
            return __awaiter(this, void 0, void 0, function* () {
                var _a;
                const apiUrl = (_a = this.ctx.config.get(exports.NewVolsegVolumeServerConfig.DefaultServer)) !== null && _a !== void 0 ? _a : api_1.DEFAULT_VOLSEG_SERVER;
                const api = new api_1.VolumeApiV2(apiUrl);
                const entryLists = yield api.getEntryList(10 ** 6);
                Object.values(entryLists).forEach(l => l.sort());
                this.ctx.customState.volsegAvailableEntries = entryLists;
            });
        }
    }
});
exports.LoadVolseg = mol_state_1.StateAction.build({
    display: { name: 'Load Volume & Segmentation' },
    from: objects_1.PluginStateObject.Root,
    params: (a, plugin) => {
        const res = (0, entry_root_1.createLoadVolsegParams)(plugin, plugin.customState.volsegAvailableEntries);
        return res;
    },
})(({ params, state }, ctx) => mol_task_1.Task.create('Loading Volume & Segmentation', taskCtx => {
    return state.transaction(() => __awaiter(void 0, void 0, void 0, function* () {
        const entryParams = entry_root_1.VolsegEntryParamValues.fromLoadVolsegParamValues(params);
        if (entryParams.entryId.trim().length === 0) {
            alert('Must specify Entry Id!');
            throw new Error('Specify Entry Id');
        }
        if (!entryParams.entryId.includes('-')) {
            // add source prefix if the user omitted it (e.g. 1832 -> emd-1832)
            entryParams.entryId = (0, helpers_1.createEntryId)(entryParams.source, entryParams.entryId);
        }
        ctx.behaviors.layout.leftPanelTabName.next('data');
        const globalStateNode = ctx.state.data.selectQ(q => q.ofType(global_state_1.VolsegGlobalState))[0];
        if (!globalStateNode) {
            yield state.build().toRoot().apply(transformers_1.VolsegGlobalStateFromRoot, {}, { state: { isGhost: !DEBUGGING } }).commit();
        }
        const entryNode = yield state.build().toRoot().apply(transformers_1.VolsegEntryFromRoot, entryParams).commit();
        yield state.build().to(entryNode).apply(transformers_1.VolsegStateFromEntry, {}, { state: { isGhost: !DEBUGGING } }).commit();
        if (entryNode.data) {
            const entryData = entryNode.data;
            const hasVolumes = entryNode.data.metadata.value.raw.grid.volumes.volume_sampling_info.spatial_downsampling_levels.length > 0;
            if (hasVolumes) {
                const group = yield entryNode.data.volumeData.createVolumeGroup();
                const updatedChannelsData = [];
                const results = [];
                const channelIds = entryNode.data.metadata.value.raw.grid.volumes.channel_ids;
                for (const channelId of channelIds) {
                    const volumeParams = { timeframeIndex: 0, channelId: channelId };
                    const volumeNode = yield state.build().to(group).apply(transformers_1.ProjectVolumeData, volumeParams, { tags: [entry_root_1.VOLUME_NODE_TAG] }).commit();
                    const result = yield entryNode.data.volumeData.createVolumeRepresentation3D(volumeNode, volumeParams);
                    results.push(result);
                }
                for (const result of results) {
                    if (result) {
                        const isovalue = result.isovalue.kind === 'relative' ? result.isovalue.relativeValue : result.isovalue.absoluteValue;
                        updatedChannelsData.push({ channelId: result.channelId, volumeIsovalueKind: result.isovalue.kind, volumeIsovalueValue: isovalue, volumeType: result.volumeType, volumeOpacity: result.opacity,
                            label: result.label,
                            color: result.color
                        });
                    }
                }
                yield entryNode.data.updateStateNode({ channelsData: [...updatedChannelsData] });
            }
            const hasLattices = entryNode.data.metadata.value.raw.grid.segmentation_lattices;
            if (hasLattices && hasLattices.segmentation_ids.length > 0) {
                const group = yield entryNode.data.latticeSegmentationData.createSegmentationGroup();
                const segmentationIds = hasLattices.segmentation_ids;
                for (const segmentationId of segmentationIds) {
                    const descriptionsForLattice = entryNode.data.metadata.value.getDescriptions(segmentationId, 'lattice', 0);
                    const segmentLabels = (0, utils_1.getSegmentLabelsFromDescriptions)(descriptionsForLattice);
                    const segmentationParams = {
                        timeframeIndex: 0,
                        segmentationId: segmentationId,
                        segmentLabels: segmentLabels,
                        ownerId: entryNode.data.ref
                    };
                    const segmentationNode = yield state.build().to(group).apply(transformers_1.ProjectSegmentationData, segmentationParams, { tags: [entry_root_1.LATTICE_SEGMENTATION_NODE_TAG] }).commit();
                    yield entryNode.data.latticeSegmentationData.createSegmentationRepresentation3D(segmentationNode, segmentationParams);
                }
            }
            ;
            const hasMeshes = entryNode.data.metadata.value.raw.grid.segmentation_meshes;
            if (hasMeshes && hasMeshes.segmentation_ids.length > 0) {
                const group = yield entryNode.data.meshSegmentationData.createMeshGroup();
                const segmentationIds = hasMeshes.segmentation_ids;
                for (const segmentationId of segmentationIds) {
                    const timeframeIndex = 0;
                    const meshSegmentParams = entryData.meshSegmentationData.getMeshSegmentParams(segmentationId, timeframeIndex);
                    const meshParams = {
                        meshSegmentParams: meshSegmentParams,
                        segmentationId: segmentationId,
                        timeframeIndex: timeframeIndex
                    };
                    const meshNode = yield state.build().to(group).apply(transformers_1.ProjectMeshData, meshParams, { tags: [entry_root_1.MESH_SEGMENTATION_NODE_TAG] }).commit();
                    yield entryNode.data.meshSegmentationData.createMeshRepresentation3D(meshNode, meshParams);
                }
            }
            const hasGeometricSegmentation = entryData.metadata.value.raw.grid.geometric_segmentation;
            if (hasGeometricSegmentation && hasGeometricSegmentation.segmentation_ids.length > 0) {
                const group = yield entryNode.data.geometricSegmentationData.createGeometricSegmentationGroup();
                // const timeInfo = this.entryData.metadata.value!.raw.grid.geometric_segmentation!.time_info;
                for (const segmentationId of hasGeometricSegmentation.segmentation_ids) {
                    const timeframeIndex = 0;
                    const geometricSegmentationParams = {
                        segmentationId: segmentationId,
                        timeframeIndex: timeframeIndex
                    };
                    const geometricSegmentationNode = yield state.build().to(group).apply(transformers_1.ProjectGeometricSegmentationData, geometricSegmentationParams, { tags: [entry_root_1.GEOMETRIC_SEGMENTATION_NODE_TAG] }).commit();
                    yield entryNode.data.geometricSegmentationData.createGeometricSegmentationRepresentation3D(geometricSegmentationNode, geometricSegmentationParams);
                }
            }
            const allAnnotationsForTimeframe = entryData.metadata.value.getAllAnnotations(0);
            const allSegmentKeysForTimeframe = allAnnotationsForTimeframe.map(a => {
                return (0, utils_1.createSegmentKey)(a.segment_id, a.segmentation_id, a.segment_kind);
            });
            yield (0, common_1.actionShowSegments)(allSegmentKeysForTimeframe, entryData);
        }
    })).runInContext(taskCtx);
}));
