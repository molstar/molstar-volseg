"use strict";
/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Adam Midlik <midlik@gmail.com>
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
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
exports.VolsegEntryData = exports.RawMeshSegmentData = exports.VolsegEntry = exports.VolsegEntryParamValues = exports.createVolsegEntryParams = exports.createLoadVolsegParams = exports.LATTICE_SEGMENTATION_NODE_TAG = exports.VOLUME_NODE_TAG = exports.BOX = exports.MAX_VOXELS = exports.MESH_SEGMENTATION_NODE_TAG = exports.GEOMETRIC_SEGMENTATION_NODE_TAG = void 0;
const rxjs_1 = require("rxjs");
const _1 = require(".");
const shape_1 = require("molstar/lib/mol-model/shape");
const volume_1 = require("molstar/lib/mol-model/volume");
const objects_1 = require("molstar/lib/mol-plugin-state/objects");
const behavior_1 = require("molstar/lib/mol-plugin/behavior");
const commands_1 = require("molstar/lib/mol-plugin/commands");
const mol_state_1 = require("molstar/lib/mol-state");
const mol_util_1 = require("molstar/lib/mol-util");
const param_definition_1 = require("molstar/lib/mol-util/param-definition");
const mesh_extension_1 = require("../meshes/mesh-extension");
const api_1 = require("./volseg-api/api");
const utils_1 = require("./volseg-api/utils");
const entry_meshes_1 = require("./entry-meshes");
const entry_models_1 = require("./entry-models");
const entry_segmentation_1 = require("./entry-segmentation");
const entry_state_1 = require("./entry-state");
const entry_volume_1 = require("./entry-volume");
const ExternalAPIs = __importStar(require("./external-api"));
const global_state_1 = require("./global-state");
const helpers_1 = require("./helpers");
const assets_1 = require("molstar/lib/mol-util/assets");
const component_1 = require("molstar/lib/mol-plugin-state/component");
const entry_geometric_segmentation_1 = require("./entry-geometric-segmentation");
const shape_primitives_1 = require("./shape_primitives");
const common_1 = require("../common");
const zip_1 = require("molstar/lib/mol-util/zip/zip");
const data_1 = require("../cvsx-extension/data");
const common_2 = require("../common");
exports.GEOMETRIC_SEGMENTATION_NODE_TAG = 'geometric-segmentation-node';
exports.MESH_SEGMENTATION_NODE_TAG = 'mesh-segmentation-node';
exports.MAX_VOXELS = 10 ** 7;
// export const MAX_VOXELS = 10 ** 2; // DEBUG
exports.BOX = null;
// export const BOX: [[number, number, number], [number, number, number]] | null = [[-90, -90, -90], [90, 90, 90]]; // DEBUG
exports.VOLUME_NODE_TAG = 'volume-node-tag';
exports.LATTICE_SEGMENTATION_NODE_TAG = 'segmenation-node-tag';
function createLoadVolsegParams(plugin, entrylists = {}) {
    var _a;
    const defaultVolumeServer = (_a = plugin === null || plugin === void 0 ? void 0 : plugin.config.get(_1.NewVolsegVolumeServerConfig.DefaultServer)) !== null && _a !== void 0 ? _a : api_1.DEFAULT_VOLSEG_SERVER;
    return {
        serverUrl: param_definition_1.ParamDefinition.Text(defaultVolumeServer),
        source: param_definition_1.ParamDefinition.Mapped(common_2.SourceChoice.values[0], common_2.SourceChoice.options, src => entryParam(entrylists[src])),
    };
}
exports.createLoadVolsegParams = createLoadVolsegParams;
function entryParam(entries = []) {
    const options = entries.map(e => [e, e]);
    options.push(['__custom__', 'Custom']);
    return param_definition_1.ParamDefinition.Group({
        entryId: param_definition_1.ParamDefinition.Select(options[0][0], options, { description: 'Choose an entry from the list, or choose "Custom" and type any entry ID (useful when using other than default server).' }),
        customEntryId: param_definition_1.ParamDefinition.Text('', { hideIf: p => p.entryId !== '__custom__', description: 'Entry identifier, including the source prefix, e.g. "emd-1832"' }),
    }, { isFlat: true });
}
function createVolsegEntryParams(plugin) {
    var _a;
    const defaultVolumeServer = (_a = plugin === null || plugin === void 0 ? void 0 : plugin.config.get(_1.NewVolsegVolumeServerConfig.DefaultServer)) !== null && _a !== void 0 ? _a : api_1.DEFAULT_VOLSEG_SERVER;
    return {
        serverUrl: param_definition_1.ParamDefinition.Text(defaultVolumeServer),
        source: common_2.SourceChoice.PDSelect(),
        entryId: param_definition_1.ParamDefinition.Text('emd-1832', { description: 'Entry identifier, including the source prefix, e.g. "emd-1832"' }),
    };
}
exports.createVolsegEntryParams = createVolsegEntryParams;
var VolsegEntryParamValues;
(function (VolsegEntryParamValues) {
    function fromLoadVolsegParamValues(params) {
        let entryId = params.source.params.entryId;
        if (entryId === '__custom__') {
            entryId = params.source.params.customEntryId;
        }
        return {
            serverUrl: params.serverUrl,
            source: params.source.name,
            entryId: entryId
        };
    }
    VolsegEntryParamValues.fromLoadVolsegParamValues = fromLoadVolsegParamValues;
})(VolsegEntryParamValues || (exports.VolsegEntryParamValues = VolsegEntryParamValues = {}));
class VolsegEntry extends objects_1.PluginStateObject.CreateBehavior({ name: 'Vol & Seg Entry' }) {
}
exports.VolsegEntry = VolsegEntry;
class RawMeshSegmentData {
    constructor(segmentId, data) {
        this.segmentId = segmentId;
        this.data = data;
        // super();
    }
}
exports.RawMeshSegmentData = RawMeshSegmentData;
class RawChannelData extends component_1.PluginComponent {
    constructor(timeframeIndex, channelId, data) {
        super();
        this.timeframeIndex = timeframeIndex;
        this.channelId = channelId;
        this.data = data;
    }
}
class RawSegmentationData extends component_1.PluginComponent {
    constructor(timeframeIndex, segmentationId, data) {
        super();
        this.timeframeIndex = timeframeIndex;
        this.segmentationId = segmentationId;
        this.data = data;
    }
}
class RawTimeframesDataCache {
    constructor(entryData, kind) {
        this.entryData = entryData;
        this.kind = kind;
        this.cache = new Map();
        this.totalSizeLimitInBytes = 1000000000;
    }
    setCacheSizeInItems(data) {
        if (!this.maxEntries) {
            const size = this._getEntrySize(data);
            this._setCacheSizeInItems(size);
        }
    }
    _createKey(timeframeIndex, channelIdOrSegmentationId) {
        return `${timeframeIndex.toString()}_${channelIdOrSegmentationId}`;
    }
    _getEntrySize(entry) {
        const data = entry.data;
        let bytes = 0;
        if (data instanceof Uint8Array) {
            bytes = data.length;
        }
        else if (data instanceof String) {
            // string
            bytes = new TextEncoder().encode(data).length;
        }
        else if ((0, utils_1.instanceOfShapePrimitiveData)(data)) {
            bytes = JSON.stringify(data).length;
        }
        else {
            // rawMeshSegmentData
            const arr = data;
            for (const i of arr) {
                const b = this._getEntrySize(i);
                bytes = bytes + b;
            }
        }
        return bytes;
    }
    _setCacheSizeInItems(entrySizeInBytes) {
        const limit = this.totalSizeLimitInBytes / entrySizeInBytes;
        this.maxEntries = Math.round(limit);
    }
    ;
    add(data) {
        if (this.cache.size >= this.maxEntries) {
            // least-recently used cache eviction strategy
            const keyToDelete = this.cache.keys().next().value;
            this.cache.delete(keyToDelete);
        }
        // check if exists
        const timeframeIndex = data.timeframeIndex;
        let key;
        if (data instanceof RawChannelData) {
            key = this._createKey(timeframeIndex, data.channelId);
        }
        else if (data instanceof RawSegmentationData) {
            key = this._createKey(timeframeIndex, data.segmentationId);
        }
        else {
            throw Error(`data type ${data}is not supported`);
        }
        const hasKey = this.cache.has(key);
        if (hasKey) {
            return null;
        }
        else {
            // add
            this.cache.set(key, data);
            this.setCacheSizeInItems(data);
        }
    }
    get(timeframeIndex, channelIdOrSegmentationId, kind) {
        return __awaiter(this, void 0, void 0, function* () {
            const key = this._createKey(timeframeIndex, channelIdOrSegmentationId);
            // check if exists
            const hasKey = this.cache.has(key);
            if (hasKey) {
                // peek the entry, re-insert for LRU strategy
                const entry = this.cache.get(key);
                this.cache.delete(key);
                this.cache.set(key, entry);
                return entry;
            }
            else {
                if (this.cache.size >= this.maxEntries) {
                    // least-recently used cache eviction strategy
                    const keyToDelete = this.cache.keys().next().value;
                    this.cache.delete(keyToDelete);
                }
                let entry;
                if (kind === 'volume') {
                    entry = yield this.entryData._loadRawChannelData(timeframeIndex, channelIdOrSegmentationId);
                }
                else if (kind === 'segmentation') {
                    entry = yield this.entryData._loadRawLatticeSegmentationData(timeframeIndex, channelIdOrSegmentationId);
                }
                else if (kind === 'mesh') {
                    entry = yield this.entryData._loadRawMeshSegmentationData(timeframeIndex, channelIdOrSegmentationId);
                }
                else if (kind === 'primitive') {
                    entry = yield this.entryData._loadGeometricSegmentationData(timeframeIndex, channelIdOrSegmentationId);
                }
                else {
                    throw Error(`Data kind ${kind} is not supported`);
                }
                this.cache.delete(key);
                this.cache.set(key, entry);
                this.setCacheSizeInItems(entry);
                return entry;
            }
        });
    }
}
class VolsegEntryData extends behavior_1.PluginBehavior.WithSubscribers {
    constructor(plugin, params, filesData) {
        super(plugin, params);
        this.ref = '';
        this.kind = 'api';
        this.filesData = undefined;
        this.metadata = new rxjs_1.BehaviorSubject(undefined);
        this.cachedVolumeTimeframesData = new RawTimeframesDataCache(this, 'volume');
        this.cachedSegmentationTimeframesData = new RawTimeframesDataCache(this, 'segmentation');
        this.cachedMeshesTimeframesData = new RawTimeframesDataCache(this, 'mesh');
        this.cachedShapePrimitiveData = new RawTimeframesDataCache(this, 'primitive');
        this.state = {
            hierarchy: new rxjs_1.BehaviorSubject(undefined)
        };
        this.volumeData = new entry_volume_1.VolsegVolumeData(this);
        this.geometricSegmentationData = new entry_geometric_segmentation_1.VolsegGeometricSegmentationData(this);
        this.latticeSegmentationData = new entry_segmentation_1.VolsegLatticeSegmentationData(this);
        this.meshSegmentationData = new entry_meshes_1.VolsegMeshSegmentationData(this);
        this.modelData = new entry_models_1.VolsegModelData(this);
        this.highlightRequest = new rxjs_1.Subject();
        this.getStateNode = (0, helpers_1.lazyGetter)(() => this.plugin.state.data.selectQ(q => q.byRef(this.ref).subtree().ofType(entry_state_1.VolsegState))[0], 'Missing VolsegState node. Must first create VolsegState for this VolsegEntry.');
        this.currentState = new rxjs_1.BehaviorSubject(param_definition_1.ParamDefinition.getDefaultValues(entry_state_1.VolsegStateParams));
        this.currentVolume = new rxjs_1.BehaviorSubject([]);
        this.currentTimeframe = new rxjs_1.BehaviorSubject(0);
        this.labelProvider = {
            label: (loci) => {
                var _a;
                const segmentId = this.getSegmentIdFromLoci(loci);
                const segmentationId = this.getSegmentationIdFromLoci(loci);
                const segmentationKind = this.getSegmentationKindFromLoci(loci);
                if (segmentId === undefined || !segmentationId || !segmentationKind)
                    return;
                const descriptions = this.metadata.value.getSegmentDescription(segmentId, segmentationId, segmentationKind);
                if (!descriptions)
                    return;
                const descriptionName = descriptions[0].name;
                const segmentName = descriptionName;
                const annotLabels = (_a = descriptions[0].external_references) === null || _a === void 0 ? void 0 : _a.map(e => `${(0, helpers_1.applyEllipsis)(e.label ? e.label : '')} [${e.resource}:${e.accession}]`);
                if (descriptions[0].is_hidden === true)
                    return;
                let onHoverLabel = '';
                if (segmentName)
                    onHoverLabel = onHoverLabel + '<hr class="msp-highlight-info-hr"/>' + '<b>' + segmentName + '</b>';
                if (annotLabels && annotLabels.length > 0)
                    onHoverLabel = onHoverLabel + '<hr class="msp-highlight-info-hr"/>' + annotLabels.filter(helpers_1.isDefined).join('<br/>');
                if (onHoverLabel !== '')
                    return onHoverLabel;
                else
                    return;
            }
        };
        this.plugin = plugin;
        this.api = new api_1.VolumeApiV2(params.serverUrl);
        this.source = params.source;
        this.entryId = params.entryId;
        this.entryNumber = (0, helpers_1.splitEntryId)(this.entryId).entryNumber;
        this.filesData = filesData;
    }
    initialize() {
        return __awaiter(this, void 0, void 0, function* () {
            var _a, _b;
            const metadata = yield this.api.getMetadata(this.source, this.entryId);
            this.metadata.next(new utils_1.MetadataWrapper(metadata));
            this.pdbs = yield ExternalAPIs.getPdbIdsForEmdbEntry((_b = (_a = this.metadata.value.raw.annotation) === null || _a === void 0 ? void 0 : _a.entry_id.source_db_id) !== null && _b !== void 0 ? _b : this.entryId);
            yield this.init();
        });
    }
    initializeFromFile(metadata) {
        return __awaiter(this, void 0, void 0, function* () {
            if (metadata)
                this.metadata.next(new utils_1.MetadataWrapper(metadata));
            yield this.initFromFile();
        });
    }
    static create(plugin, params) {
        return __awaiter(this, void 0, void 0, function* () {
            const result = new VolsegEntryData(plugin, params);
            yield result.initialize();
            return result;
        });
    }
    static getRawLatticeSegmentationsFromCSVX(cvsxFilesIndex, zf) {
        let rawLatticeSegmentations;
        if (cvsxFilesIndex.latticeSegmentations) {
            const condition = cvsxFilesIndex.latticeSegmentations;
            rawLatticeSegmentations = zf.filter(z => condition.hasOwnProperty(z[0]));
        }
        return rawLatticeSegmentations;
    }
    ;
    static getRawGeometricSegmentationsFromCVSX(cvsxFilesIndex, zf) {
        let rawGeometricSegmentations;
        if (cvsxFilesIndex.geometricSegmentations) {
            const condition = cvsxFilesIndex.geometricSegmentations;
            rawGeometricSegmentations = zf.filter(z => condition.hasOwnProperty(z[0]));
        }
        return rawGeometricSegmentations;
    }
    static getRawMeshSegmentationsFromCSVX(cvsxFilesIndex, zf) {
        let rawMeshSegmentations;
        if (cvsxFilesIndex.meshSegmentations) {
            const condition = cvsxFilesIndex.meshSegmentations;
            if (condition) {
                rawMeshSegmentations = new Array;
                for (const meshSegmentation of condition) {
                    const targetData = zf.filter(z => {
                        const filenames = meshSegmentation.segmentsFilenames;
                        if (filenames.includes(z[0])) {
                            return z;
                        }
                    });
                    rawMeshSegmentations = rawMeshSegmentations.concat(targetData);
                }
            }
            ;
        }
        return rawMeshSegmentations;
    }
    static createFromFile(plugin, file, runtimeCtx) {
        return __awaiter(this, void 0, void 0, function* () {
            const zippedFiles = yield (0, zip_1.unzip)(runtimeCtx, file.buffer);
            const zf = Object.entries(zippedFiles);
            const indexJsonEntry = zf.find(z => z[0] === 'index.json');
            if (!indexJsonEntry) {
                throw new Error('No index.json found, CVSX has wrong content');
            }
            const cvsxFilesIndex = yield (0, common_1.parseCVSXJSON)(indexJsonEntry, plugin);
            // obligatory components
            const rawQueryJSON = zf.find(z => z[0] === cvsxFilesIndex.query);
            const metadataJSONEntry = zf.find(z => z[0] === cvsxFilesIndex.metadata);
            const annotationJSONEntry = zf.find(z => z[0] === cvsxFilesIndex.annotations);
            const rawVolumes = zf.filter(z => cvsxFilesIndex.volumes.hasOwnProperty(z[0]));
            const rawLatticeSegmentations = this.getRawLatticeSegmentationsFromCSVX(cvsxFilesIndex, zf);
            const rawMeshSegmentations = this.getRawMeshSegmentationsFromCSVX(cvsxFilesIndex, zf);
            const rawGeometricSegmentations = this.getRawGeometricSegmentationsFromCVSX(cvsxFilesIndex, zf);
            if (!rawQueryJSON || !metadataJSONEntry || !annotationJSONEntry) {
                throw new Error('CVSX has wrong content, some obligatory components are missing');
            }
            // do parsing
            const parsedQueryJSON = yield (0, common_1.parseCVSXJSON)(rawQueryJSON, plugin);
            let params = {
                serverUrl: '',
                source: parsedQueryJSON.source_db,
                entryId: parsedQueryJSON.entry_id,
            };
            const parsedGridMetadata = yield (0, common_1.parseCVSXJSON)(metadataJSONEntry, plugin);
            const parsedAnnotationMetadata = yield (0, common_1.parseCVSXJSON)(annotationJSONEntry, plugin);
            const source = parsedGridMetadata.entry_id.source_db_name;
            const entryId = parsedGridMetadata.entry_id.source_db_id;
            params = {
                serverUrl: '',
                source: source,
                entryId: entryId
            };
            const metadata = {
                grid: parsedGridMetadata,
                annotation: parsedAnnotationMetadata
            };
            const cvsxData = new data_1.CVSXData(cvsxFilesIndex, plugin);
            const filesData = {
                volumes: cvsxData.volumeDataFromRaw(rawVolumes),
                latticeSegmentations: cvsxData.latticeSegmentationDataFromRaw(rawLatticeSegmentations),
                meshSegmentations: cvsxData.meshSegmentationDataFromRaw(rawMeshSegmentations),
                geometricSegmentations: yield cvsxData.geometricSegmentationDataFromRaw(rawGeometricSegmentations),
                annotations: parsedAnnotationMetadata,
                metadata: parsedGridMetadata,
                query: parsedQueryJSON,
                index: cvsxFilesIndex
            };
            const result = new VolsegEntryData(plugin, params, filesData);
            yield result.initializeFromFile(metadata);
            return result;
        });
    }
    getData(timeframeIndex, channelIdOrSegmentationId, kind) {
        return __awaiter(this, void 0, void 0, function* () {
            if (kind === 'volume') {
                const channelData = yield this.cachedVolumeTimeframesData.get(timeframeIndex, channelIdOrSegmentationId, 'volume');
                return channelData.data;
            }
            else if (kind === 'segmentation') {
                const segmentationData = yield this.cachedSegmentationTimeframesData.get(timeframeIndex, channelIdOrSegmentationId, 'segmentation');
                return segmentationData.data;
            }
            else if (kind === 'mesh') {
                const meshData = yield this.cachedMeshesTimeframesData.get(timeframeIndex, channelIdOrSegmentationId, 'mesh');
                return meshData.data;
            }
            else if (kind === 'primitive') {
                const shapePrimitiveData = yield this.cachedShapePrimitiveData.get(timeframeIndex, channelIdOrSegmentationId, 'primitive');
                return shapePrimitiveData.data;
            }
        });
    }
    sync() {
        const volumes = this.findNodesByTags(exports.VOLUME_NODE_TAG);
        const segmentations = this.findNodesByTags(exports.LATTICE_SEGMENTATION_NODE_TAG);
        const geometricSegmentations = this.findNodesByTags(exports.GEOMETRIC_SEGMENTATION_NODE_TAG);
        const meshSegmentations = this.findNodesByTags(exports.MESH_SEGMENTATION_NODE_TAG);
        this.state.hierarchy.next({ volumes, segmentations, geometricSegmentations, meshSegmentations });
    }
    init() {
        return __awaiter(this, void 0, void 0, function* () {
            this.sync();
            this.subscribeObservable(this.plugin.state.data.events.changed, state => {
                this.sync();
            });
            const hasVolumes = this.metadata.value.raw.grid.volumes.volume_sampling_info.spatial_downsampling_levels.length > 0;
            if (hasVolumes) {
                yield this.preloadVolumeTimeframesData();
            }
            const hasLattices = this.metadata.value.raw.grid.segmentation_lattices;
            if (hasLattices) {
                yield this.preloadSegmentationTimeframesData();
            }
            const hasMeshes = this.metadata.value.raw.grid.segmentation_meshes;
            if (hasMeshes) {
                yield this.preloadMeshesTimeframesData();
            }
            const hasShapePrimitives = this.metadata.value.raw.grid.geometric_segmentation;
            if (hasShapePrimitives) {
                yield this.preloadMeshesTimeframesData();
            }
        });
    }
    initFromFile() {
        return __awaiter(this, void 0, void 0, function* () {
            this.kind = 'file';
            this.sync();
            this.subscribeObservable(this.plugin.state.data.events.changed, state => {
                this.sync();
            });
            const hasVolumes = this.metadata.value.raw.grid.volumes.volume_sampling_info.spatial_downsampling_levels.length > 0;
            if (hasVolumes) {
                this.preloadVolumeTimeframesDataFromFile();
            }
            const hasLattices = this.metadata.value.raw.grid.segmentation_lattices;
            if (hasLattices) {
                this.preloadSegmentationTimeframesDataFromFile();
            }
            const hasGeometricSegmentation = this.metadata.value.raw.grid.geometric_segmentation;
            if (hasGeometricSegmentation) {
                this.preloadShapePrimitivesTimeframesDataFromFile();
            }
            const hasMeshes = this.metadata.value.raw.grid.segmentation_meshes;
            if (hasMeshes) {
                this.preloadMeshTimeframesDataFromFile();
            }
        });
    }
    updateMetadata() {
        return __awaiter(this, void 0, void 0, function* () {
            const metadata = yield this.api.getMetadata(this.source, this.entryId);
            this.metadata.next(new utils_1.MetadataWrapper(metadata));
        });
    }
    register(ref) {
        return __awaiter(this, void 0, void 0, function* () {
            var _a;
            this.ref = ref;
            this.plugin.managers.lociLabels.addProvider(this.labelProvider);
            try {
                const params = (_a = this.getStateNode().obj) === null || _a === void 0 ? void 0 : _a.data;
                if (params) {
                    this.currentState.next(params);
                }
            }
            catch (_b) {
                // do nothing
            }
            const volumeVisual = this.findNodesByTags(entry_volume_1.VOLUME_VISUAL_TAG)[0];
            if (volumeVisual)
                this.addCurrentVolume(volumeVisual.transform);
            const volumeRefs = new Set();
            this.subscribeObservable(this.plugin.state.data.events.cell.stateUpdated, e => {
                var _a, _b;
                try {
                    (this.getStateNode());
                }
                catch (_c) {
                    return;
                } // if state not does not exist yet
                if (e.cell.transform.ref === this.getStateNode().transform.ref) {
                    const newState = (_a = this.getStateNode().obj) === null || _a === void 0 ? void 0 : _a.data;
                    if (newState && !(0, mol_util_1.shallowEqualObjects)(newState, this.currentState.value)) { // avoid repeated update
                        this.currentState.next(newState);
                    }
                }
                else if ((_b = e.cell.transform.tags) === null || _b === void 0 ? void 0 : _b.includes(entry_volume_1.VOLUME_VISUAL_TAG)) {
                    if (volumeRefs.has(e.ref)) {
                        this.addCurrentVolume(e.cell.transform);
                    }
                    else if (mol_state_1.StateSelection.findAncestor(this.plugin.state.data.tree, this.plugin.state.data.cells, e.ref, a => a.transform.ref === ref)) {
                        volumeRefs.add(e.ref);
                        this.addCurrentVolume(e.cell.transform);
                    }
                }
            });
            this.subscribeObservable(this.plugin.state.data.events.cell.removed, e => {
                if (volumeRefs.has(e.ref)) {
                    volumeRefs.delete(e.ref);
                    this.removeCurrentVolume(e.ref);
                }
            });
            this.subscribeObservable(this.plugin.behaviors.interaction.click, (e) => __awaiter(this, void 0, void 0, function* () {
                if (e.current.loci.kind === 'empty-loci')
                    return;
                const loci = e.current.loci;
                const clickedSegmentId = this.getSegmentIdFromLoci(loci);
                const clickedSegmentSegmentationId = this.getSegmentationIdFromLoci(loci);
                const segmentationKind = this.getSegmentationKindFromLoci(loci);
                if (clickedSegmentSegmentationId === undefined)
                    return;
                if (clickedSegmentId === undefined)
                    return;
                if (segmentationKind === undefined)
                    return;
                const clickedSegmentKey = (0, utils_1.createSegmentKey)(clickedSegmentId, clickedSegmentSegmentationId, segmentationKind);
                if (clickedSegmentKey === this.currentState.value.selectedSegment) {
                    (0, common_1.actionSelectSegment)(this, undefined);
                }
                else {
                    (0, common_1.actionSelectSegment)(this, clickedSegmentKey);
                }
            }));
            this.subscribeObservable(this.highlightRequest.pipe((0, rxjs_1.throttleTime)(50, undefined, { leading: true, trailing: true })), (segmentKey) => __awaiter(this, void 0, void 0, function* () { return yield this.highlightSegment(segmentKey); }));
            this.subscribeObservable(this.currentState.pipe((0, rxjs_1.distinctUntilChanged)((a, b) => a.selectedSegment === b.selectedSegment)), (state) => __awaiter(this, void 0, void 0, function* () {
                var _c;
                if ((_c = global_state_1.VolsegGlobalStateData.getGlobalState(this.plugin)) === null || _c === void 0 ? void 0 : _c.selectionMode)
                    yield this.selectSegment(state.selectedSegment);
            }));
        });
    }
    unregister() {
        return __awaiter(this, void 0, void 0, function* () {
            this.plugin.managers.lociLabels.removeProvider(this.labelProvider);
        });
    }
    removeSegmentAnnotation(segmentId, segmentationId, kind) {
        return __awaiter(this, void 0, void 0, function* () {
            const targetAnnotation = this.metadata.value.getSegmentAnnotation(segmentId, segmentationId, kind);
            this.api.removeSegmentAnnotationsUrl(this.source, this.entryId, [targetAnnotation.id]);
            this.metadata.value.removeSegmentAnnotation(targetAnnotation.id);
        });
    }
    removeDescription(descriptionId) {
        return __awaiter(this, void 0, void 0, function* () {
            this.api.removeDescriptionsUrl(this.source, this.entryId, [descriptionId]);
            this.metadata.value.removeDescription(descriptionId);
        });
    }
    editDescriptions(descriptionData) {
        return __awaiter(this, void 0, void 0, function* () {
            yield this.api.editDescriptionsUrl(this.source, this.entryId, descriptionData);
        });
    }
    editSegmentAnnotations(segmentAnnotationData) {
        return __awaiter(this, void 0, void 0, function* () {
            yield this.api.editSegmentAnnotationsUrl(this.source, this.entryId, segmentAnnotationData);
        });
    }
    _resolveBinaryUrl(urlString) {
        return __awaiter(this, void 0, void 0, function* () {
            const url = assets_1.Asset.getUrlAsset(this.plugin.managers.asset, urlString);
            const asset = this.plugin.managers.asset.resolve(url, 'binary');
            const data = (yield asset.run()).data;
            return data;
        });
    }
    _resolveStringUrl(urlString) {
        return __awaiter(this, void 0, void 0, function* () {
            const url = assets_1.Asset.getUrlAsset(this.plugin.managers.asset, urlString);
            const asset = this.plugin.managers.asset.resolve(url, 'string');
            const data = (yield asset.run()).data;
            return data;
        });
    }
    _loadRawMeshSegmentationData(timeframe, segmentationId) {
        return __awaiter(this, void 0, void 0, function* () {
            const segmentsData = [];
            const segmentsToCreate = this.metadata.value.getMeshSegmentIdsForSegmentationIdAndTimeframe(segmentationId, timeframe);
            for (const seg of segmentsToCreate) {
                const detail = this.metadata.value.getSufficientMeshDetail(segmentationId, timeframe, seg, entry_meshes_1.DEFAULT_MESH_DETAIL);
                const urlString = this.api.meshUrl_Bcif(this.source, this.entryId, segmentationId, timeframe, seg, detail);
                const data = yield this._resolveBinaryUrl(urlString);
                segmentsData.push(new RawMeshSegmentData(seg, data));
            }
            return new RawSegmentationData(timeframe, segmentationId, segmentsData);
        });
    }
    _loadGeometricSegmentationData(timeframe, segmentationId) {
        return __awaiter(this, void 0, void 0, function* () {
            const url = this.api.geometricSegmentationUrl(this.source, this.entryId, segmentationId, timeframe);
            const primitivesData = yield this._resolveStringUrl(url);
            const parsedData = JSON.parse(primitivesData);
            return new RawSegmentationData(timeframe, segmentationId, parsedData);
        });
    }
    _loadRawChannelData(timeframe, channelId) {
        return __awaiter(this, void 0, void 0, function* () {
            const urlString = this.api.volumeUrl(this.source, this.entryId, timeframe, channelId, exports.BOX, exports.MAX_VOXELS);
            const data = yield this._resolveBinaryUrl(urlString);
            return new RawChannelData(timeframe, channelId, data);
        });
    }
    _loadRawLatticeSegmentationData(timeframe, segmentationId) {
        return __awaiter(this, void 0, void 0, function* () {
            const urlString = this.api.latticeUrl(this.source, this.entryId, segmentationId, timeframe, exports.BOX, exports.MAX_VOXELS);
            const data = yield this._resolveBinaryUrl(urlString);
            return new RawSegmentationData(timeframe, segmentationId, data);
        });
    }
    loadRawChannelsData(timeInfo, channelIds) {
        return __awaiter(this, void 0, void 0, function* () {
            const start = timeInfo.start;
            const end = timeInfo.end;
            for (let i = start; i <= end; i++) {
                for (const channelId of channelIds) {
                    const rawChannelData = yield this._loadRawChannelData(i, channelId);
                    this.cachedVolumeTimeframesData.add(rawChannelData);
                }
            }
        });
    }
    loadRawLatticeSegmentationData(timeInfoMapping, segmentationIds) {
        return __awaiter(this, void 0, void 0, function* () {
            for (const segmentationId of segmentationIds) {
                const timeInfo = timeInfoMapping[segmentationId];
                const start = timeInfo.start;
                const end = timeInfo.end;
                for (let i = start; i <= end; i++) {
                    const rawLatticeSegmentationData = yield this._loadRawLatticeSegmentationData(i, segmentationId);
                    this.cachedSegmentationTimeframesData.add(rawLatticeSegmentationData);
                }
            }
        });
    }
    loadRawMeshSegmentationData(timeInfoMapping, segmentationIds) {
        return __awaiter(this, void 0, void 0, function* () {
            for (const segmentationId of segmentationIds) {
                const timeInfo = timeInfoMapping[segmentationId];
                const start = timeInfo.start;
                const end = timeInfo.end;
                for (let i = start; i <= end; i++) {
                    const rawMeshSegmentationData = yield this._loadRawMeshSegmentationData(i, segmentationId);
                    this.cachedMeshesTimeframesData.add(rawMeshSegmentationData);
                }
            }
        });
    }
    loadRawShapePrimitiveData(timeInfoMapping, segmentationIds) {
        return __awaiter(this, void 0, void 0, function* () {
            for (const segmentationId of segmentationIds) {
                const timeInfo = timeInfoMapping[segmentationId];
                const start = timeInfo.start;
                const end = timeInfo.end;
                for (let i = start; i <= end; i++) {
                    const shapePrimitiveData = yield this._loadGeometricSegmentationData(i, segmentationId);
                    this.cachedShapePrimitiveData.add(shapePrimitiveData);
                }
            }
        });
    }
    preloadVolumeTimeframesData() {
        return __awaiter(this, void 0, void 0, function* () {
            const timeInfo = this.metadata.value.raw.grid.volumes.time_info;
            const channelIds = this.metadata.value.raw.grid.volumes.channel_ids;
            this.loadRawChannelsData(timeInfo, channelIds);
        });
    }
    preloadSegmentationTimeframesDataFromFile() {
        // const latticesMeta = this.metadata.value!.hasLatticeSegmentations();
        if (this.filesData.latticeSegmentations) {
            for (const v of this.filesData.latticeSegmentations) {
                const rawLatticeSegmentationData = new RawSegmentationData(v.timeframeIndex, v.segmentationId, v.data);
                // channelsData.push(rawChannelData);
                this.cachedSegmentationTimeframesData.add(rawLatticeSegmentationData);
            }
        }
    }
    preloadShapePrimitivesTimeframesDataFromFile() {
        //
        if (this.filesData.geometricSegmentations) {
            // if (this.metadata.value!.raw.grid.geometric_segmentation && this.metadata.value!.raw.grid.geometric_segmentation.segmentation_ids.length > 0) {
            for (const g of this.filesData.geometricSegmentations) {
                const shapePrimitiveData = new RawSegmentationData(g.timeframeIndex, g.segmentationId, g.data);
                // channelsData.push(rawChannelData);
                this.cachedShapePrimitiveData.add(shapePrimitiveData);
            }
        }
    }
    preloadMeshTimeframesDataFromFile() {
        if (this.filesData.meshSegmentations) {
            for (const segmentationData of this.filesData.meshSegmentations) {
                const segmentsData = [];
                const rawData = segmentationData.data;
                for (const [filename, d] of rawData) {
                    const segmentId = parseInt(filename.split('_')[1]);
                    segmentsData.push(new RawMeshSegmentData(segmentId, d));
                }
                const data = new RawSegmentationData(segmentationData.timeframeIndex, segmentationData.segmentationId, segmentsData);
                this.cachedMeshesTimeframesData.add(data);
            }
        }
    }
    preloadVolumeTimeframesDataFromFile() {
        // need to iterate over all volumes
        for (const v of this.filesData.volumes) {
            const rawChannelData = new RawChannelData(v.timeframeIndex, v.channelId, v.data);
            this.cachedVolumeTimeframesData.add(rawChannelData);
        }
    }
    preloadSegmentationTimeframesData() {
        return __awaiter(this, void 0, void 0, function* () {
            if (this.metadata.value.raw.grid.segmentation_lattices) {
                const segmentationIds = this.metadata.value.raw.grid.segmentation_lattices.segmentation_ids;
                const timeInfoMapping = this.metadata.value.raw.grid.segmentation_lattices.time_info;
                this.loadRawLatticeSegmentationData(timeInfoMapping, segmentationIds);
            }
        });
    }
    preloadMeshesTimeframesData() {
        return __awaiter(this, void 0, void 0, function* () {
            if (this.metadata.value.raw.grid.segmentation_meshes) {
                const segmentationIds = this.metadata.value.raw.grid.segmentation_meshes.segmentation_ids;
                const timeInfoMapping = this.metadata.value.raw.grid.segmentation_meshes.time_info;
                this.loadRawMeshSegmentationData(timeInfoMapping, segmentationIds);
            }
        });
    }
    preloadShapePrimitivesTimeframesData() {
        return __awaiter(this, void 0, void 0, function* () {
            if (this.metadata.value.raw.grid.geometric_segmentation) {
                const segmentationIds = this.metadata.value.raw.grid.geometric_segmentation.segmentation_ids;
                const timeInfoMapping = this.metadata.value.raw.grid.geometric_segmentation.time_info;
                this.loadRawShapePrimitiveData(timeInfoMapping, segmentationIds);
            }
        });
    }
    updateProjectData(timeframeIndex) {
        return __awaiter(this, void 0, void 0, function* () {
            this.changeCurrentTimeframe(timeframeIndex);
            const volumes = this.state.hierarchy.value.volumes;
            const segmenations = this.state.hierarchy.value.segmentations;
            const geometricSegmentations = this.state.hierarchy.value.geometricSegmentations;
            const meshSegmentations = this.state.hierarchy.value.meshSegmentations;
            for (const v of volumes) {
                const projectDataTransform = v.transform.ref;
                const oldParams = v.transform.params;
                const params = {
                    channelId: oldParams.channelId,
                    timeframeIndex: timeframeIndex
                };
                yield this.plugin.state.updateTransform(this.plugin.state.data, projectDataTransform, params, 'Project Data Transform');
            }
            for (const s of segmenations) {
                const projectSegmentationDataTransform = s.transform.ref;
                const oldParams = s.transform.params;
                const descriptionsForLattice = this.metadata.value.getDescriptions(oldParams.segmentationId, 'lattice', this.currentTimeframe.value);
                const segmentLabels = (0, utils_1.getSegmentLabelsFromDescriptions)(descriptionsForLattice);
                const newParams = Object.assign(Object.assign({}, oldParams), { segmentLabels: segmentLabels, timeframeIndex: timeframeIndex });
                yield this.plugin.state.updateTransform(this.plugin.state.data, projectSegmentationDataTransform, newParams, 'Project Data Transform');
            }
            for (const s of geometricSegmentations) {
                const transform = s.transform.ref;
                const oldParams = s.transform.params;
                const newParams = Object.assign(Object.assign({}, oldParams), { 
                    // segmentLabels: segmentLabels,
                    timeframeIndex: timeframeIndex });
                yield this.plugin.state.updateTransform(this.plugin.state.data, transform, newParams, 'Project Data Transform');
            }
            for (const m of meshSegmentations) {
                const transform = m.transform.ref;
                const oldParams = m.transform.params;
                const newParams = Object.assign(Object.assign({}, oldParams), { timeframeIndex: timeframeIndex });
                yield this.plugin.state.updateTransform(this.plugin.state.data, transform, newParams, 'Project Data Transform');
            }
        });
    }
    changeCurrentTimeframe(index) {
        this.currentTimeframe.next(index);
    }
    addCurrentVolume(t) {
        const current = this.currentVolume.value;
        const next = [];
        let added = false;
        for (const v of current) {
            if (v.ref === t.ref) {
                next.push(t);
                added = true;
            }
            else {
                next.push(v);
            }
        }
        if (!added)
            next.push(t);
        this.currentVolume.next(next);
    }
    removeCurrentVolume(ref) {
        const current = this.currentVolume.value;
        const next = [];
        for (const v of current) {
            if (v.ref !== ref) {
                next.push(v);
            }
        }
        this.currentVolume.next(next);
    }
    actionHighlightSegment(segmentKey) {
        this.highlightRequest.next(segmentKey);
    }
    actionSetOpacity(opacity, segmentationId, kind) {
        return __awaiter(this, void 0, void 0, function* () {
            if (kind === 'lattice')
                this.latticeSegmentationData.updateOpacity(opacity, segmentationId);
            else if (kind === 'mesh')
                this.meshSegmentationData.updateOpacity(opacity, segmentationId);
            else if (kind === 'primitive')
                this.geometricSegmentationData.updateOpacity(opacity, segmentationId);
        });
    }
    actionShowFittedModel(pdbIds) {
        return __awaiter(this, void 0, void 0, function* () {
            yield this.modelData.showPdbs(pdbIds);
            yield this.updateStateNode({ visibleModels: pdbIds.map(pdbId => ({ pdbId: pdbId })) });
        });
    }
    actionSetVolumeVisual(type, channelId, transform) {
        return __awaiter(this, void 0, void 0, function* () {
            yield this.volumeData.setVolumeVisual(type, channelId, transform);
            const currentChannelsData = this.currentState.value.channelsData;
            const channelToBeUpdated = currentChannelsData.filter(c => c.channelId === channelId)[0];
            channelToBeUpdated.volumeType = type;
            yield this.updateStateNode({ channelsData: [...currentChannelsData] });
        });
    }
    actionUpdateVolumeVisual(params, channelId, transform) {
        return __awaiter(this, void 0, void 0, function* () {
            yield this.volumeData.updateVolumeVisual(params, channelId, transform);
            const currentChannelsData = this.currentState.value.channelsData;
            const channelToBeUpdated = currentChannelsData.filter(c => c.channelId === channelId)[0];
            channelToBeUpdated.volumeType = params.volumeType;
            channelToBeUpdated.volumeOpacity = params.opacity;
            yield this.updateStateNode({ channelsData: [...currentChannelsData] });
        });
    }
    highlightSegment(segmentKey) {
        return __awaiter(this, void 0, void 0, function* () {
            yield commands_1.PluginCommands.Interactivity.ClearHighlights(this.plugin);
            if (segmentKey) {
                const parsedSegmentKey = (0, utils_1.parseSegmentKey)(segmentKey);
                const { segmentId, segmentationId, kind } = parsedSegmentKey;
                if (kind === 'lattice') {
                    yield this.latticeSegmentationData.highlightSegment(segmentId, segmentationId);
                }
                else if (kind === 'mesh') {
                    yield this.meshSegmentationData.highlightSegment(segmentId, segmentationId);
                }
                else if (kind === 'primitive') {
                    yield this.geometricSegmentationData.highlightSegment(segmentId, segmentationId);
                }
            }
        });
    }
    selectSegment(segmentKey) {
        return __awaiter(this, void 0, void 0, function* () {
            this.plugin.managers.interactivity.lociSelects.deselectAll();
            const parsedSegmentKey = (0, utils_1.parseSegmentKey)(segmentKey);
            if (parsedSegmentKey.kind === 'lattice') {
                yield this.latticeSegmentationData.selectSegment(parsedSegmentKey.segmentId, parsedSegmentKey.segmentationId);
            }
            else if (parsedSegmentKey.kind === 'mesh') {
                yield this.meshSegmentationData.selectSegment(parsedSegmentKey.segmentId, parsedSegmentKey.segmentationId);
            }
            else if (parsedSegmentKey.kind === 'primitive') {
                yield this.geometricSegmentationData.selectSegment(parsedSegmentKey.segmentId, parsedSegmentKey.segmentationId);
            }
            yield this.highlightSegment();
        });
    }
    updateStateNode(params) {
        return __awaiter(this, void 0, void 0, function* () {
            const oldParams = this.getStateNode().transform.params;
            const newParams = Object.assign(Object.assign({}, oldParams), params);
            const state = this.plugin.state.data;
            const update = state.build().to(this.getStateNode().transform.ref).update(newParams);
            yield commands_1.PluginCommands.State.Update(this.plugin, { state, tree: update, options: { doNotUpdateCurrent: true } });
        });
    }
    findNodesByRef(ref) {
        return this.plugin.state.data.selectQ(q => q.byRef(ref).subtree())[0];
    }
    /** Find the nodes under this entry root which have all of the given tags. */
    findNodesByTags(...tags) {
        return this.plugin.state.data.selectQ(q => {
            let builder = q.byRef(this.ref).subtree();
            for (const tag of tags)
                builder = builder.withTag(tag);
            return builder;
        });
    }
    newUpdate() {
        if (this.ref !== '') {
            return this.plugin.build().to(this.ref);
        }
        else {
            return this.plugin.build().toRoot();
        }
    }
    getSegmentationIdFromLoci(loci) {
        var _a, _b;
        if (volume_1.Volume.Segment.isLoci(loci)) {
            return loci.volume.label;
        }
        else if (shape_1.ShapeGroup.isLoci(loci)) {
            const sourceData = loci.shape.sourceData;
            if ((0, mesh_extension_1.isMeshlistData)(sourceData)) {
                const meshData = ((_a = loci.shape.sourceData) !== null && _a !== void 0 ? _a : {});
                return meshData.segmentationId;
            }
            else if ((0, shape_primitives_1.isShapePrimitiveParamsValues)(sourceData)) {
                const shapePrimitiveParamsValues = ((_b = loci.shape.sourceData) !== null && _b !== void 0 ? _b : {});
                return shapePrimitiveParamsValues.segmentationId;
            }
        }
    }
    getSegmentationKindFromLoci(loci) {
        if (volume_1.Volume.Segment.isLoci(loci)) {
            return 'lattice';
        }
        else if (shape_1.ShapeGroup.isLoci(loci)) {
            const sourceData = loci.shape.sourceData;
            if ((0, mesh_extension_1.isMeshlistData)(sourceData)) {
                return 'mesh';
            }
            else if ((0, shape_primitives_1.isShapePrimitiveParamsValues)(sourceData)) {
                return 'primitive';
            }
        }
    }
    getSegmentIdFromLoci(loci) {
        var _a, _b;
        if (volume_1.Volume.Segment.isLoci(loci) && loci.volume._propertyData.ownerId === this.ref) {
            if (loci.segments.length === 1) {
                return loci.segments[0];
            }
        }
        if (shape_1.ShapeGroup.isLoci(loci)) {
            const sourceData = loci.shape.sourceData;
            if ((0, mesh_extension_1.isMeshlistData)(sourceData)) {
                const meshData = ((_a = loci.shape.sourceData) !== null && _a !== void 0 ? _a : {});
                if (meshData.ownerId === this.ref && meshData.segmentId !== undefined) {
                    return meshData.segmentId;
                }
            }
            else if ((0, shape_primitives_1.isShapePrimitiveParamsValues)(sourceData)) {
                const shapePrimitiveParamsValues = ((_b = loci.shape.sourceData) !== null && _b !== void 0 ? _b : {});
                return shapePrimitiveParamsValues.segmentId;
            }
        }
    }
    setTryUseGpu(tryUseGpu) {
        return __awaiter(this, void 0, void 0, function* () {
            yield Promise.all([
                this.volumeData.setTryUseGpu(tryUseGpu),
                this.latticeSegmentationData.setTryUseGpu(tryUseGpu),
            ]);
        });
    }
    setSelectionMode(selectSegments) {
        return __awaiter(this, void 0, void 0, function* () {
            if (selectSegments) {
                yield this.selectSegment(this.currentState.value.selectedSegment);
            }
            else {
                this.plugin.managers.interactivity.lociSelects.deselectAll();
            }
        });
    }
}
exports.VolsegEntryData = VolsegEntryData;
