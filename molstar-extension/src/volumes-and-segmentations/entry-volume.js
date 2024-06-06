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
exports.VolsegVolumeData = exports.SimpleVolumeParams = exports.VOLUME_VISUAL_TAG = void 0;
const linear_algebra_1 = require("molstar/lib/mol-math/linear-algebra");
const volume_1 = require("molstar/lib/mol-model/volume");
const volume_representation_params_1 = require("molstar/lib/mol-plugin-state/helpers/volume-representation-params");
const transforms_1 = require("molstar/lib/mol-plugin-state/transforms");
const misc_1 = require("molstar/lib/mol-plugin-state/transforms/misc");
const state_1 = require("molstar/lib/mol-plugin/behavior/static/state");
const commands_1 = require("molstar/lib/mol-plugin/commands");
const param_definition_1 = require("molstar/lib/mol-util/param-definition");
const entry_state_1 = require("./entry-state");
const ExternalAPIs = __importStar(require("./external-api"));
const global_state_1 = require("./global-state");
const GROUP_TAG = 'volume-group';
exports.VOLUME_VISUAL_TAG = 'volume-visual';
const DIRECT_VOLUME_RELATIVE_PEAK_HALFWIDTH = 0.5;
;
exports.SimpleVolumeParams = {
    volumeType: entry_state_1.VolumeTypeChoice.PDSelect(),
    opacity: param_definition_1.ParamDefinition.Numeric(0.2, { min: 0, max: 1, step: 0.05 }, { hideIf: p => p.volumeType === 'off' }),
};
class VolsegVolumeData {
    constructor(rootData) {
        this.visualTypeParamCache = {};
        this.entryData = rootData;
    }
    createVolumeGroup() {
        return __awaiter(this, void 0, void 0, function* () {
            var _a;
            let group = (_a = this.entryData.findNodesByTags(GROUP_TAG)[0]) === null || _a === void 0 ? void 0 : _a.transform.ref;
            if (!group) {
                const newGroupNode = yield this.entryData.newUpdate().apply(misc_1.CreateGroup, { label: 'Volume' }, { tags: [GROUP_TAG], state: { isCollapsed: true } }).commit();
                group = newGroupNode.ref;
            }
            return group;
        });
    }
    createVolumeRepresentation3D(volumeNode, params) {
        return __awaiter(this, void 0, void 0, function* () {
            var _a, _b, _c, _d, _e;
            const { channelId } = params;
            const isoLevelPromise = ExternalAPIs.tryGetIsovalue((_b = (_a = this.entryData.metadata.value.raw.annotation) === null || _a === void 0 ? void 0 : _a.entry_id.source_db_id) !== null && _b !== void 0 ? _b : this.entryData.entryId);
            const color = this.entryData.metadata.value.getVolumeChannelColor(channelId);
            const volumeData = volumeNode.cell.obj.data;
            let label = this.entryData.metadata.value.getVolumeChannelLabel(channelId);
            if (!label)
                label = channelId.toString();
            const volumeType = entry_state_1.VolumeTypeChoice.defaultValue;
            let isovalue = yield isoLevelPromise;
            if (!isovalue) {
                const stats = volumeData.grid.stats;
                const maxRelative = (stats.max - stats.mean) / stats.sigma;
                if (maxRelative > 1) {
                    isovalue = { kind: 'relative', value: 1.0 };
                }
                else {
                    isovalue = { kind: 'relative', value: maxRelative * 0.5 };
                }
            }
            const adjustedIsovalue = volume_1.Volume.adjustedIsoValue(volumeData, isovalue.value, isovalue.kind);
            const visualParams = this.createVolumeVisualParams(volumeData, volumeType, color);
            this.changeIsovalueInVolumeVisualParams(visualParams, adjustedIsovalue, volumeData.grid.stats, channelId);
            const volumeRepresentation3D = yield this.entryData.newUpdate()
                .to(volumeNode)
                .apply(transforms_1.StateTransforms.Representation.VolumeRepresentation3D, visualParams, { tags: [exports.VOLUME_VISUAL_TAG] })
                .commit();
            const transform = (_c = volumeRepresentation3D.cell) === null || _c === void 0 ? void 0 : _c.transform;
            if (!transform)
                return null;
            const volumeValues = {
                volumeType: transform.state.isHidden ? 'off' : (_d = transform.params) === null || _d === void 0 ? void 0 : _d.type.name,
                opacity: (_e = transform.params) === null || _e === void 0 ? void 0 : _e.type.params.alpha,
            };
            return { isovalue: adjustedIsovalue, volumeType: volumeValues.volumeType, opacity: volumeValues.opacity, channelId: channelId, label: label, color: color };
        });
    }
    setVolumeVisual(type, channelId, transform) {
        return __awaiter(this, void 0, void 0, function* () {
            var _a, _b;
            const visual = this.entryData.findNodesByRef(transform.ref);
            if (!visual)
                return;
            const oldParams = visual.transform.params;
            this.visualTypeParamCache[oldParams.type.name] = oldParams.type.params;
            if (type === 'off') {
                (0, state_1.setSubtreeVisibility)(this.entryData.plugin.state.data, visual.transform.ref, true); // true means hide, ¯\_(ツ)_/¯
            }
            else {
                (0, state_1.setSubtreeVisibility)(this.entryData.plugin.state.data, visual.transform.ref, false); // true means hide, ¯\_(ツ)_/¯
                if (oldParams.type.name === type)
                    return;
                const newParams = Object.assign(Object.assign({}, oldParams), { type: {
                        name: type,
                        params: (_a = this.visualTypeParamCache[type]) !== null && _a !== void 0 ? _a : oldParams.type.params,
                    } });
                const volumeStats = (_b = visual.obj) === null || _b === void 0 ? void 0 : _b.data.sourceData.grid.stats;
                if (!volumeStats)
                    throw new Error(`Cannot get volume stats from volume visual ${visual.transform.ref}`);
                this.changeIsovalueInVolumeVisualParams(newParams, undefined, volumeStats, channelId);
                const update = this.entryData.newUpdate().to(visual.transform.ref).update(newParams);
                yield commands_1.PluginCommands.State.Update(this.entryData.plugin, { state: this.entryData.plugin.state.data, tree: update, options: { doNotUpdateCurrent: true } });
            }
        });
    }
    updateVolumeVisual(newParams, channelId, transform) {
        return __awaiter(this, void 0, void 0, function* () {
            var _a, _b;
            const { volumeType, opacity } = newParams;
            const visual = this.entryData.findNodesByRef(transform.ref);
            if (!visual)
                return;
            const oldVisualParams = visual.transform.params;
            this.visualTypeParamCache[oldVisualParams.type.name] = oldVisualParams.type.params;
            if (volumeType === 'off') {
                (0, state_1.setSubtreeVisibility)(this.entryData.plugin.state.data, visual.transform.ref, true); // true means hide, ¯\_(ツ)_/¯
            }
            else {
                (0, state_1.setSubtreeVisibility)(this.entryData.plugin.state.data, visual.transform.ref, false); // true means hide, ¯\_(ツ)_/¯
                const newVisualParams = Object.assign(Object.assign({}, oldVisualParams), { type: {
                        name: volumeType,
                        params: (_a = this.visualTypeParamCache[volumeType]) !== null && _a !== void 0 ? _a : oldVisualParams.type.params,
                    } });
                newVisualParams.type.params.alpha = opacity;
                const volumeStats = (_b = visual.obj) === null || _b === void 0 ? void 0 : _b.data.sourceData.grid.stats;
                if (!volumeStats)
                    throw new Error(`Cannot get volume stats from volume visual ${visual.transform.ref}`);
                this.changeIsovalueInVolumeVisualParams(newVisualParams, undefined, volumeStats, channelId);
                const update = this.entryData.newUpdate().to(visual.transform.ref).update(newVisualParams);
                yield commands_1.PluginCommands.State.Update(this.entryData.plugin, { state: this.entryData.plugin.state.data, tree: update, options: { doNotUpdateCurrent: true } });
            }
        });
    }
    setTryUseGpu(tryUseGpu) {
        return __awaiter(this, void 0, void 0, function* () {
            const visuals = this.entryData.findNodesByTags(exports.VOLUME_VISUAL_TAG);
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
    getIsovalueFromState(channelId) {
        const { volumeIsovalueKind, volumeIsovalueValue } = this.entryData.currentState.value.channelsData.filter(c => c.channelId === channelId)[0];
        return volumeIsovalueKind === 'relative'
            ? volume_1.Volume.IsoValue.relative(volumeIsovalueValue)
            : volume_1.Volume.IsoValue.absolute(volumeIsovalueValue);
    }
    createVolumeVisualParams(volume, type, color) {
        var _a;
        if (type === 'off')
            type = 'isosurface';
        const dimensions = volume.grid.cells.space.dimensions;
        const dimensionsOrder = {
            0: 'x',
            1: 'y',
            2: 'z'
        };
        for (const i in dimensions) {
            if (dimensions[i] === 1) {
                const params = (0, volume_representation_params_1.createVolumeRepresentationParams)(this.entryData.plugin, volume, {
                    type: 'slice',
                    typeParams: { dimension: { name: dimensionsOrder[i], params: 0 }, isoValue: { kind: 'relative', relativeValue: 0 } },
                    color: 'uniform',
                    colorParams: { value: color },
                });
                return params;
            }
        }
        return (0, volume_representation_params_1.createVolumeRepresentationParams)(this.entryData.plugin, volume, {
            type: type,
            typeParams: { alpha: 0.2, tryUseGpu: (_a = global_state_1.VolsegGlobalStateData.getGlobalState(this.entryData.plugin)) === null || _a === void 0 ? void 0 : _a.tryUseGpu },
            color: 'uniform',
            colorParams: { value: color },
        });
    }
    changeIsovalueInVolumeVisualParams(params, isovalue, stats, channelId) {
        var _a;
        isovalue !== null && isovalue !== void 0 ? isovalue : (isovalue = this.getIsovalueFromState(channelId));
        switch (params.type.name) {
            case 'isosurface':
                params.type.params.isoValue = isovalue;
                params.type.params.tryUseGpu = (_a = global_state_1.VolsegGlobalStateData.getGlobalState(this.entryData.plugin)) === null || _a === void 0 ? void 0 : _a.tryUseGpu;
                break;
            case 'direct-volume':
                const absIso = volume_1.Volume.IsoValue.toAbsolute(isovalue, stats).absoluteValue;
                const fractIso = (absIso - stats.min) / (stats.max - stats.min);
                const peakHalfwidth = DIRECT_VOLUME_RELATIVE_PEAK_HALFWIDTH * stats.sigma / (stats.max - stats.min);
                params.type.params.controlPoints = [
                    linear_algebra_1.Vec2.create(Math.max(fractIso - peakHalfwidth, 0), 0),
                    linear_algebra_1.Vec2.create(fractIso, 1),
                    linear_algebra_1.Vec2.create(Math.min(fractIso + peakHalfwidth, 1), 0),
                ];
                break;
        }
    }
}
exports.VolsegVolumeData = VolsegVolumeData;
