"use strict";
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
exports.VolsegGlobalStateFromRoot = exports.VolsegGlobalStateFromFile = exports.VolsegStateFromEntry = exports.VolsegEntryFromFile = exports.VolsegEntryFromRoot = exports.ProjectGeometricSegmentationData = exports.ProjectGeometricSegmentationDataParams = exports.ProjectMeshData = exports.ProjectSegmentationData = exports.ProjectVolumeData = exports.ProjectMeshSegmentationDataParams = exports.ProjectLatticeSegmentationDataParams = exports.ProjectDataParams = void 0;
/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Adam Midlik <midlik@gmail.com>
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */
const cif_1 = require("molstar/lib/mol-io/reader/cif");
const density_server_1 = require("molstar/lib/mol-model-formats/volume/density-server");
const segmentation_1 = require("molstar/lib/mol-model-formats/volume/segmentation");
const objects_1 = require("molstar/lib/mol-plugin-state/objects");
const mol_state_1 = require("molstar/lib/mol-state");
const mol_task_1 = require("molstar/lib/mol-task");
const param_definition_1 = require("molstar/lib/mol-util/param-definition");
const mesh_extension_1 = require("../meshes/mesh-extension");
const entry_root_1 = require("./entry-root");
const entry_state_1 = require("./entry-state");
const global_state_1 = require("./global-state");
const helpers_1 = require("./helpers");
const shape_primitives_1 = require("./shape_primitives");
exports.ProjectDataParams = {
    timeframeIndex: param_definition_1.ParamDefinition.Numeric(0, { step: 1 }),
    channelId: param_definition_1.ParamDefinition.Text('0'),
};
exports.ProjectLatticeSegmentationDataParams = {
    timeframeIndex: param_definition_1.ParamDefinition.Numeric(0, { step: 1 }),
    segmentationId: param_definition_1.ParamDefinition.Text('0'),
    segmentLabels: param_definition_1.ParamDefinition.ObjectList({ id: param_definition_1.ParamDefinition.Numeric(-1), label: param_definition_1.ParamDefinition.Text('') }, s => `${s.id} = ${s.label}`, { description: 'Mapping of segment IDs to segment labels' }),
    ownerId: param_definition_1.ParamDefinition.Text('', { isHidden: true, description: 'Reference to the object which manages this volume' }),
};
exports.ProjectMeshSegmentationDataParams = Object.assign({ timeframeIndex: param_definition_1.ParamDefinition.Numeric(0, { step: 1 }), segmentationId: param_definition_1.ParamDefinition.Text('0') }, mesh_extension_1.VolsegMeshDataParams);
exports.ProjectVolumeData = (0, helpers_1.CreateTransformer)({
    name: 'project-volume-data',
    display: { name: 'Project Volume Data', description: 'Project Volume Data' },
    from: objects_1.PluginStateObject.Root,
    to: objects_1.PluginStateObject.Volume.Data,
    params: exports.ProjectDataParams
})({
    apply({ a, params, spine }, plugin) {
        return mol_task_1.Task.create('Project Volume Data', (ctx) => __awaiter(this, void 0, void 0, function* () {
            const { timeframeIndex, channelId } = params;
            const entry = spine.getAncestorOfType(entry_root_1.VolsegEntry);
            const entryData = entry.data;
            const rawData = yield entryData.getData(timeframeIndex, channelId, 'volume');
            let label = entryData.metadata.value.getVolumeChannelLabel(channelId);
            if (!label)
                label = channelId.toString();
            const parsed = yield cif_1.CIF.parse(rawData).runInContext(ctx);
            if (parsed.isError)
                throw new Error(parsed.message);
            const cif = new objects_1.PluginStateObject.Format.Cif(parsed.result);
            const header = cif.data.blocks[1].header; // zero block contains query meta-data
            const block = cif.data.blocks.find(b => b.header === header);
            if (!block)
                throw new Error(`Data block '${[header]}' not found.`);
            const volumeCif = cif_1.CIF.schema.densityServer(block);
            const volume = yield (0, density_server_1.volumeFromDensityServerData)(volumeCif).runInContext(ctx);
            const [x, y, z] = volume.grid.cells.space.dimensions;
            const props = { label: `Volume channel: ${label}`, description: `Volume ${x}\u00D7${y}\u00D7${z}` };
            const volumedata3dinfo = volume.sourceData.data;
            const samplerate = volumedata3dinfo.volume_data_3d_info.sample_rate;
            const downsampling = samplerate.__array[0];
            entryData.metadata.value.setCurrentlyUsedVolumeDownsampling(downsampling);
            return new objects_1.PluginStateObject.Volume.Data(volume, props);
        }));
    }
});
exports.ProjectSegmentationData = (0, helpers_1.CreateTransformer)({
    name: 'project-segmentation-data',
    display: { name: 'Project Segmentation Data', description: 'Project Segmentation Data' },
    from: objects_1.PluginStateObject.Root,
    to: objects_1.PluginStateObject.Volume.Data,
    params: exports.ProjectLatticeSegmentationDataParams
})({
    apply({ a, params, spine }, plugin) {
        return mol_task_1.Task.create('Project Volume Data', (ctx) => __awaiter(this, void 0, void 0, function* () {
            const { timeframeIndex, segmentationId } = params;
            const entry = spine.getAncestorOfType(entry_root_1.VolsegEntry);
            const entryData = entry.data;
            const rawData = yield entryData.getData(timeframeIndex, segmentationId, 'segmentation');
            const label = segmentationId;
            const parsed = yield cif_1.CIF.parse(rawData).runInContext(ctx);
            if (parsed.isError)
                throw new Error(parsed.message);
            const cif = new objects_1.PluginStateObject.Format.Cif(parsed.result);
            const header = cif.data.blocks[1].header; // zero block contains query meta-data
            const block = cif.data.blocks.find(b => b.header === header);
            if (!block)
                throw new Error(`Data block '${[header]}' not found.`);
            const segmentationCif = cif_1.CIF.schema.segmentation(block);
            const segmentLabels = {};
            for (const segment of params.segmentLabels)
                segmentLabels[segment.id] = '';
            const volume = yield (0, segmentation_1.volumeFromSegmentationData)(segmentationCif, { label: label, segmentLabels: segmentLabels, ownerId: params.ownerId }).runInContext(ctx);
            const [x, y, z] = volume.grid.cells.space.dimensions;
            const props = { label: `ID: ${label}`, description: `${label} ${x}\u00D7${y}\u00D7${z}` };
            return new objects_1.PluginStateObject.Volume.Data(volume, props);
        }));
    }
});
exports.ProjectMeshData = (0, helpers_1.CreateTransformer)({
    name: 'project-mesh-data',
    display: { name: 'Project Mesh Data', description: 'Project Mesh Data' },
    from: entry_root_1.VolsegEntry,
    to: mesh_extension_1.VolsegMeshSegmentation,
    params: exports.ProjectMeshSegmentationDataParams
})({
    apply({ a, params, spine }, plugin) {
        return mol_task_1.Task.create('Project Mesh Data', (ctx) => __awaiter(this, void 0, void 0, function* () {
            const { timeframeIndex, segmentationId } = params;
            const entry = spine.getAncestorOfType(entry_root_1.VolsegEntry);
            const entryData = entry.data;
            const meshData = [];
            const segmentsParams = params.meshSegmentParams;
            const rawDataArray = yield entryData.getData(timeframeIndex, segmentationId, 'mesh');
            for (const segmentParam of segmentsParams) {
                const rawDataItem = rawDataArray.find(i => i.segmentId === segmentParam.id);
                if (!rawDataItem)
                    throw new Error('no segment');
                const rawData = rawDataItem.data;
                const parsed = yield cif_1.CIF.parse(rawData).runInContext(ctx);
                if (parsed.isError)
                    throw new Error(parsed.message);
                // const cif = new PluginStateObject.Format.Cif(parsed.result);
                const cif = parsed.result;
                const meshDataItem = {
                    meshSegmentParams: segmentParam,
                    parsedCif: cif
                };
                meshData.push(meshDataItem);
            }
            return new mesh_extension_1.VolsegMeshSegmentation(new mesh_extension_1.VolsegMeshData(meshData), { label: `Segmentation ID: ${segmentationId}` });
        }));
    }
});
exports.ProjectGeometricSegmentationDataParams = {
    timeframeIndex: param_definition_1.ParamDefinition.Numeric(0, { step: 1 }),
    segmentationId: param_definition_1.ParamDefinition.Text('0'),
};
exports.ProjectGeometricSegmentationData = (0, helpers_1.CreateTransformer)({
    name: 'project-geometric-segmentation',
    display: { name: 'Project Geometric Segmentation', description: 'Project Geometric Segmentation' },
    from: entry_root_1.VolsegEntry,
    to: shape_primitives_1.VolsegGeometricSegmentation,
    params: exports.ProjectGeometricSegmentationDataParams
})({
    apply({ a, params, spine }, plugin) {
        return mol_task_1.Task.create('Project Geometric Segmentation Data', (ctx) => __awaiter(this, void 0, void 0, function* () {
            const { timeframeIndex, segmentationId } = params;
            const entry = spine.getAncestorOfType(entry_root_1.VolsegEntry);
            const entryData = entry.data;
            const shapePrimitiveData = yield entryData.getData(timeframeIndex, segmentationId, 'primitive');
            return new shape_primitives_1.VolsegGeometricSegmentation(new shape_primitives_1.VolsegShapePrimitivesData(shapePrimitiveData), { label: `Segmentation ID: ${segmentationId}` });
        }));
    }
});
exports.VolsegEntryFromRoot = (0, helpers_1.CreateTransformer)({
    name: 'volseg-entry-from-root',
    display: { name: 'Vol & Seg Entry', description: 'Vol & Seg Entry' },
    from: objects_1.PluginStateObject.Root,
    to: entry_root_1.VolsegEntry,
    params: (a, plugin) => (0, entry_root_1.createVolsegEntryParams)(plugin),
})({
    apply({ a, params }, plugin) {
        return mol_task_1.Task.create('Load Vol & Seg Entry', () => __awaiter(this, void 0, void 0, function* () {
            const data = yield entry_root_1.VolsegEntryData.create(plugin, params);
            return new entry_root_1.VolsegEntry(data, { label: data.entryId, description: 'Vol & Seg Entry' });
        }));
    },
    update({ b, oldParams, newParams }) {
        Object.assign(newParams, oldParams);
        console.error('Changing params of existing VolsegEntry node is not allowed');
        return mol_state_1.StateTransformer.UpdateResult.Unchanged;
    }
});
exports.VolsegEntryFromFile = (0, helpers_1.CreateTransformer)({
    name: 'volseg-entry-from-file',
    display: { name: 'Vol & Seg Entry', description: 'Vol & Seg Entry' },
    from: objects_1.PluginStateObject.Data.Binary,
    to: entry_root_1.VolsegEntry,
})({
    apply({ a, params }, plugin) {
        return mol_task_1.Task.create('Load Vol & Seg Entry', (ctx) => __awaiter(this, void 0, void 0, function* () {
            const data = yield entry_root_1.VolsegEntryData.createFromFile(plugin, a.data, ctx);
            return new entry_root_1.VolsegEntry(data, { label: data.entryId, description: 'Vol & Seg Entry' });
        }));
    },
    update({ b, oldParams, newParams }) {
        Object.assign(newParams, oldParams);
        console.error('Changing params of existing VolsegEntry node is not allowed');
        return mol_state_1.StateTransformer.UpdateResult.Unchanged;
    }
});
exports.VolsegStateFromEntry = (0, helpers_1.CreateTransformer)({
    name: entry_state_1.VOLSEG_STATE_FROM_ENTRY_TRANSFORMER_NAME,
    display: { name: 'Vol & Seg Entry State', description: 'Vol & Seg Entry State' },
    from: entry_root_1.VolsegEntry,
    to: entry_state_1.VolsegState,
    params: entry_state_1.VolsegStateParams,
})({
    apply({ a, params }, plugin) {
        return mol_task_1.Task.create('Create Vol & Seg Entry State', () => __awaiter(this, void 0, void 0, function* () {
            return new entry_state_1.VolsegState(params, { label: 'State' });
        }));
    }
});
exports.VolsegGlobalStateFromFile = (0, helpers_1.CreateTransformer)({
    name: 'volseg-global-state-from-file',
    display: { name: 'Vol & Seg Global State', description: 'Vol & Seg Global State' },
    from: objects_1.PluginStateObject.Data.Binary,
    to: global_state_1.VolsegGlobalState,
    params: global_state_1.VolsegGlobalStateParams,
})({
    apply({ a, params }, plugin) {
        return mol_task_1.Task.create('Create Vol & Seg Global State', () => __awaiter(this, void 0, void 0, function* () {
            const data = new global_state_1.VolsegGlobalStateData(plugin, params);
            return new global_state_1.VolsegGlobalState(data, { label: 'Global State', description: 'Vol & Seg Global State' });
        }));
    },
    update({ b, oldParams, newParams }) {
        b.data.currentState.next(newParams);
        return mol_state_1.StateTransformer.UpdateResult.Updated;
    }
});
exports.VolsegGlobalStateFromRoot = (0, helpers_1.CreateTransformer)({
    name: 'volseg-global-state-from-root',
    display: { name: 'Vol & Seg Global State', description: 'Vol & Seg Global State' },
    from: objects_1.PluginStateObject.Root,
    to: global_state_1.VolsegGlobalState,
    params: global_state_1.VolsegGlobalStateParams,
})({
    apply({ a, params }, plugin) {
        return mol_task_1.Task.create('Create Vol & Seg Global State', () => __awaiter(this, void 0, void 0, function* () {
            const data = new global_state_1.VolsegGlobalStateData(plugin, params);
            return new global_state_1.VolsegGlobalState(data, { label: 'Global State', description: 'Vol & Seg Global State' });
        }));
    },
    update({ b, oldParams, newParams }) {
        b.data.currentState.next(newParams);
        return mol_state_1.StateTransformer.UpdateResult.Updated;
    }
});
