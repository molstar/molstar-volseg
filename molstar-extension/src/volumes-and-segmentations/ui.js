"use strict";
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
var __rest = (this && this.__rest) || function (s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
        t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function")
        for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
            if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i]))
                t[p[i]] = s[p[i]];
        }
    return t;
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.WaitingParameterControls = exports.WaitingButton = exports.WaitingSlider = exports.SegmentationControls = exports.VolsegUI = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Adam Midlik <midlik@gmail.com>
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */
const reactjs_popup_1 = __importDefault(require("reactjs-popup"));
require("reactjs-popup/dist/index.css");
const react_1 = require("react");
// import { ParamDefinition as PD } from 'molstar/lib/mol-util/param-definition';
const base_1 = require("molstar/lib/mol-plugin-ui/base");
const common_1 = require("molstar/lib/mol-plugin-ui/controls/common");
const Icons = __importStar(require("molstar/lib/mol-plugin-ui/controls/icons"));
const parameters_1 = require("molstar/lib/mol-plugin-ui/controls/parameters");
const slider_1 = require("molstar/lib/mol-plugin-ui/controls/slider");
const use_behavior_1 = require("molstar/lib/mol-plugin-ui/hooks/use-behavior");
const update_transform_1 = require("molstar/lib/mol-plugin-ui/state/update-transform");
const mol_util_1 = require("molstar/lib/mol-util");
const param_definition_1 = require("molstar/lib/mol-util/param-definition");
const sleep_1 = require("molstar/lib/mol-util/sleep");
const entry_root_1 = require("./entry-root");
const entry_volume_1 = require("./entry-volume");
const global_state_1 = require("./global-state");
const helpers_1 = require("./helpers");
const utils_1 = require("./volseg-api/utils");
const common_2 = require("../common");
const common_ui_1 = require("../common-ui");
const jsoneditor_component_1 = require("./jsoneditor-component");
const rxjs_1 = require("rxjs");
var VolsegUIData;
(function (VolsegUIData) {
    function changeAvailableNodes(data, newNodes) {
        var _a;
        const newActiveNode = newNodes.length > data.availableNodes.length ?
            newNodes[newNodes.length - 1]
            : (_a = newNodes.find(node => { var _a; return node.data.ref === ((_a = data.activeNode) === null || _a === void 0 ? void 0 : _a.data.ref); })) !== null && _a !== void 0 ? _a : newNodes[0];
        return Object.assign(Object.assign({}, data), { availableNodes: newNodes, activeNode: newActiveNode });
    }
    VolsegUIData.changeAvailableNodes = changeAvailableNodes;
    function changeActiveNode(data, newActiveRef) {
        var _a;
        const newActiveNode = (_a = data.availableNodes.find(node => node.data.ref === newActiveRef)) !== null && _a !== void 0 ? _a : data.availableNodes[0];
        return Object.assign(Object.assign({}, data), { availableNodes: data.availableNodes, activeNode: newActiveNode });
    }
    VolsegUIData.changeActiveNode = changeActiveNode;
    function equals(data1, data2) {
        return (0, mol_util_1.shallowEqualArrays)(data1.availableNodes, data2.availableNodes) && data1.activeNode === data2.activeNode && data1.globalState === data2.globalState;
    }
    VolsegUIData.equals = equals;
})(VolsegUIData || (VolsegUIData = {}));
class VolsegUI extends base_1.CollapsableControls {
    defaultState() {
        return {
            header: 'Volume & Segmentation',
            isCollapsed: true,
            brand: { accent: 'orange', svg: Icons.ExtensionSvg },
            data: {
                globalState: undefined,
                availableNodes: [],
                activeNode: undefined,
            }
        };
    }
    renderControls() {
        return (0, jsx_runtime_1.jsx)(VolsegControls, { plugin: this.plugin, data: this.state.data, setData: d => this.setState({ data: d }) });
    }
    syncState(state) {
        var _a, _b, _c;
        const nodes = state.selectQ(q => q.ofType(entry_root_1.VolsegEntry)).map(cell => cell === null || cell === void 0 ? void 0 : cell.obj).filter(helpers_1.isDefined);
        const isHidden = nodes.length === 0;
        const newData = VolsegUIData.changeAvailableNodes(this.state.data, nodes);
        if (!((_a = this.state.data.globalState) === null || _a === void 0 ? void 0 : _a.isRegistered())) {
            const globalState = (_c = (_b = state.selectQ(q => q.ofType(global_state_1.VolsegGlobalState))[0]) === null || _b === void 0 ? void 0 : _b.obj) === null || _c === void 0 ? void 0 : _c.data;
            if (globalState)
                newData.globalState = globalState;
        }
        if (!VolsegUIData.equals(this.state.data, newData) || this.state.isHidden !== isHidden) {
            this.setState({ data: newData, isHidden: isHidden });
        }
    }
    componentDidMount() {
        this.setState({ isHidden: true, isCollapsed: false });
        this.syncState(this.plugin.state.data);
        this.subscribe((0, rxjs_1.combineLatest)([
            this.plugin.state.data.events.changed,
            this.plugin.behaviors.state.isAnimating,
        ]), ([e, isAnimating]) => {
            if (isAnimating)
                return;
            this.syncState(e.state);
        });
    }
}
exports.VolsegUI = VolsegUI;
function VolsegControls({ plugin, data, setData }) {
    var _a;
    const entryData = (_a = data.activeNode) === null || _a === void 0 ? void 0 : _a.data;
    if (!entryData) {
        return (0, jsx_runtime_1.jsx)("p", { children: "No data!" });
    }
    if (!data.globalState) {
        return (0, jsx_runtime_1.jsx)("p", { children: "No global state!" });
    }
    const params = {
        /** Reference to the active VolsegEntry node */
        entry: param_definition_1.ParamDefinition.Select(data.activeNode.data.ref, data.availableNodes.map(entry => [entry.data.ref, entry.data.entryId]))
    };
    const values = {
        entry: data.activeNode.data.ref,
    };
    const globalState = (0, use_behavior_1.useBehavior)(data.globalState.currentState);
    return (0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)(parameters_1.ParameterControls, { params: params, values: values, onChangeValues: next => setData(VolsegUIData.changeActiveNode(data, next.entry)) }), (0, jsx_runtime_1.jsx)(TimeFrameSlider, { entryData: entryData }), (0, jsx_runtime_1.jsx)(common_1.ExpandGroup, { header: 'Global options', children: (0, jsx_runtime_1.jsx)(WaitingParameterControls, { params: global_state_1.VolsegGlobalStateParams, values: globalState, onChangeValues: (next) => __awaiter(this, void 0, void 0, function* () { var _b; return yield ((_b = data.globalState) === null || _b === void 0 ? void 0 : _b.updateState(plugin, next)); }) }) }), (0, jsx_runtime_1.jsx)(VolsegEntryControls, { entryData: entryData }, entryData.ref)] });
}
function VolsegEntryControls({ entryData }) {
    var _a, _b;
    const state = (0, use_behavior_1.useBehavior)(entryData.currentState);
    const metadata = (0, use_behavior_1.useBehavior)(entryData.metadata);
    const allDescriptions = entryData.metadata.value.allDescriptions;
    const entryDescriptions = allDescriptions.filter(d => d.target_kind === 'entry');
    const parsedSelectedSegmentKey = (0, utils_1.parseSegmentKey)(state.selectedSegment);
    const { segmentationId, kind } = parsedSelectedSegmentKey;
    const visibleModels = state.visibleModels.map(model => model.pdbId);
    const allPdbs = entryData.pdbs;
    (0, use_behavior_1.useBehavior)(entryData.currentTimeframe);
    const annotationsJson = metadata.raw.annotation;
    return (0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)("div", { style: { fontWeight: 'bold', padding: 8, paddingTop: 6, paddingBottom: 4, overflow: 'hidden' }, children: (_b = (_a = metadata.raw.annotation) === null || _a === void 0 ? void 0 : _a.name) !== null && _b !== void 0 ? _b : 'Unnamed Annotation' }), entryDescriptions.length > 0 && entryDescriptions.map(e => (0, jsx_runtime_1.jsx)(common_ui_1.EntryDescriptionUI, { entryDescriptionData: e }, e.id)), (0, jsx_runtime_1.jsx)(reactjs_popup_1.default, { nested: true, trigger: (0, jsx_runtime_1.jsx)("button", { className: "msp-btn msp-btn-block", children: "Annotation Editor" }), modal: true, children: (0, jsx_runtime_1.jsx)(jsx_runtime_1.Fragment, { children: (0, jsx_runtime_1.jsx)(jsoneditor_component_1.JSONEditorComponent, { jsonData: annotationsJson, entryData: entryData }) }) }), allPdbs && allPdbs.length > 0 && (0, jsx_runtime_1.jsx)(common_1.ExpandGroup, { header: 'Fitted models in PDB', initiallyExpanded: true, children: allPdbs.map(pdb => (0, jsx_runtime_1.jsx)(WaitingButton, { onClick: () => entryData.actionShowFittedModel(visibleModels.includes(pdb) ? [] : [pdb]), style: { fontWeight: visibleModels.includes(pdb) ? 'bold' : undefined, textAlign: 'left', marginTop: 1 }, children: pdb }, pdb)) }), (0, jsx_runtime_1.jsx)(VolumeControls, { entryData: entryData }), (0, jsx_runtime_1.jsx)(SegmentationControls, { model: entryData }), (0, jsx_runtime_1.jsx)(common_ui_1.SelectedSegmentDescription, { model: entryData, targetSegmentationId: segmentationId, targetKind: kind })] });
}
function TimeFrameSlider({ entryData }) {
    const timeInfo = entryData.metadata.value.raw.grid.volumes.time_info;
    const timeInfoStart = timeInfo.start;
    const timeInfoValue = (0, use_behavior_1.useBehavior)(entryData.currentTimeframe);
    const timeInfoEnd = timeInfo.end;
    if (entryData.filesData) {
        if (entryData.filesData.query.time) {
            return null;
        }
    }
    if (timeInfoEnd === 0)
        return null;
    return (0, jsx_runtime_1.jsx)(common_1.ControlRow, { label: 'Time Frame', control: (0, jsx_runtime_1.jsx)(WaitingSlider, { min: timeInfoStart, max: timeInfoEnd, value: timeInfoValue, step: 1, onChange: (v) => __awaiter(this, void 0, void 0, function* () {
                yield entryData.updateProjectData(v);
            }) }) });
}
function VolumeChannelControls({ entryData, volume }) {
    var _a, _b;
    const projectDataTransform = volume.transform;
    if (!projectDataTransform)
        return null;
    const params = projectDataTransform.params;
    const channelId = params.channelId;
    const channelLabel = volume.obj.label;
    const childRef = entryData.plugin.state.data.tree.children.get(projectDataTransform.ref).toArray()[0];
    const volumeRepresentation3DNode = entryData.findNodesByRef(childRef);
    const transform = volumeRepresentation3DNode.transform;
    if (!transform)
        return null;
    const volumeValues = {
        volumeType: transform.state.isHidden ? 'off' : (_a = transform.params) === null || _a === void 0 ? void 0 : _a.type.name,
        opacity: (_b = transform.params) === null || _b === void 0 ? void 0 : _b.type.params.alpha,
    };
    return (0, jsx_runtime_1.jsxs)(common_1.ExpandGroup, { header: `${channelLabel}`, children: [(0, jsx_runtime_1.jsx)(WaitingParameterControls, { params: entry_volume_1.SimpleVolumeParams, values: volumeValues, onChangeValues: (next) => __awaiter(this, void 0, void 0, function* () { yield (0, sleep_1.sleep)(20); yield entryData.actionUpdateVolumeVisual(next, channelId, transform); }) }), (0, jsx_runtime_1.jsx)(update_transform_1.UpdateTransformControl, { state: entryData.plugin.state.data, transform: transform, customHeader: 'none' })] });
}
function _getVisualTransformFromProjectDataTransform(model, projectDataTransform) {
    const childRef = model.plugin.state.data.tree.children.get(projectDataTransform.ref).toArray()[0];
    const segmentationRepresentation3DNode = (0, common_2.findNodesByRef)(model.plugin, childRef);
    const transform = segmentationRepresentation3DNode.transform;
    if (transform.params.descriptions) {
        const childChildRef = model.plugin.state.data.tree.children.get(segmentationRepresentation3DNode.transform.ref).toArray()[0];
        const t = (0, common_2.findNodesByRef)(model.plugin, childChildRef);
        return t.transform;
    }
    else {
        return transform;
    }
}
function SegmentationSetControls({ model, segmentation, kind }) {
    var _a, _b;
    const projectDataTransform = segmentation.transform;
    if (!projectDataTransform)
        return null;
    const params = projectDataTransform.params;
    const segmentationId = params.segmentationId;
    const transform = _getVisualTransformFromProjectDataTransform(model, projectDataTransform);
    if (!transform)
        return null;
    let opacity = undefined;
    if ((_a = transform.params) === null || _a === void 0 ? void 0 : _a.type) {
        opacity = (_b = transform.params) === null || _b === void 0 ? void 0 : _b.type.params.alpha;
    }
    else {
        opacity = transform.params.alpha;
    }
    return (0, jsx_runtime_1.jsxs)(common_1.ExpandGroup, { header: `${segmentationId}`, children: [(0, jsx_runtime_1.jsx)(common_1.ControlRow, { label: 'Opacity', control: (0, jsx_runtime_1.jsx)(WaitingSlider, { min: 0, max: 1, value: opacity, step: 0.05, onChange: (v) => __awaiter(this, void 0, void 0, function* () { return yield model.actionSetOpacity(v, segmentationId, kind); }) }) }), (0, jsx_runtime_1.jsx)(common_ui_1.DescriptionsList, { model: model, targetSegmentationId: segmentationId, targetKind: kind })] });
}
function VolumeControls({ entryData }) {
    const h = (0, use_behavior_1.useBehavior)(entryData.state.hierarchy);
    if (!h)
        return null;
    const isBusy = (0, use_behavior_1.useBehavior)(entryData.plugin.behaviors.state.isBusy);
    if (isBusy) {
        return null;
    }
    return (0, jsx_runtime_1.jsx)(jsx_runtime_1.Fragment, { children: (0, jsx_runtime_1.jsx)(common_1.ExpandGroup, { header: 'Volume data', children: h.volumes.map((v) => {
                const params = v.transform.params;
                return (0, jsx_runtime_1.jsx)(VolumeChannelControls, { entryData: entryData, volume: v }, params.channelId);
            }) }) });
}
function SegmentationControls({ model }) {
    if (!model.metadata.value.hasSegmentations()) {
        return null;
    }
    const h = (0, use_behavior_1.useBehavior)(model.state.hierarchy);
    if (!h)
        return null;
    const isBusy = (0, use_behavior_1.useBehavior)(model.plugin.behaviors.state.isBusy);
    if (isBusy) {
        return null;
    }
    return (0, jsx_runtime_1.jsx)(jsx_runtime_1.Fragment, { children: (0, jsx_runtime_1.jsxs)(common_1.ExpandGroup, { header: 'Segmentation data', children: [h.segmentations.map((v) => {
                    return (0, jsx_runtime_1.jsx)(SegmentationSetControls, { model: model, segmentation: v, kind: 'lattice' }, v.transform.ref);
                }), h.meshSegmentations.map((v) => {
                    return (0, jsx_runtime_1.jsx)(SegmentationSetControls, { model: model, segmentation: v, kind: 'mesh' }, v.transform.ref);
                }), h.geometricSegmentations.map((v) => {
                    return (0, jsx_runtime_1.jsx)(SegmentationSetControls, { model: model, segmentation: v, kind: 'primitive' }, v.transform.ref);
                })] }) });
}
exports.SegmentationControls = SegmentationControls;
function WaitingSlider(_a) {
    var { value, onChange } = _a, etc = __rest(_a, ["value", "onChange"]);
    const [changing, sliderValue, execute] = useAsyncChange(value);
    return (0, jsx_runtime_1.jsx)(slider_1.Slider, Object.assign({ value: sliderValue, disabled: changing, onChange: newValue => execute(onChange, newValue) }, etc));
}
exports.WaitingSlider = WaitingSlider;
function WaitingButton(_a) {
    var { onClick } = _a, etc = __rest(_a, ["onClick"]);
    const [changing, _, execute] = useAsyncChange(undefined);
    return (0, jsx_runtime_1.jsx)(common_1.Button, Object.assign({ disabled: changing, onClick: () => execute(onClick, undefined) }, etc, { children: etc.children }));
}
exports.WaitingButton = WaitingButton;
function WaitingParameterControls(_a) {
    var { values, onChangeValues } = _a, etc = __rest(_a, ["values", "onChangeValues"]);
    const [changing, currentValues, execute] = useAsyncChange(values);
    return (0, jsx_runtime_1.jsx)(parameters_1.ParameterControls, Object.assign({ isDisabled: changing, values: currentValues, onChangeValues: newValue => execute(onChangeValues, newValue) }, etc));
}
exports.WaitingParameterControls = WaitingParameterControls;
function useAsyncChange(initialValue) {
    const [isExecuting, setIsExecuting] = (0, react_1.useState)(false);
    const [value, setValue] = (0, react_1.useState)(initialValue);
    const isMounted = (0, react_1.useRef)(false);
    (0, react_1.useEffect)(() => setValue(initialValue), [initialValue]);
    (0, react_1.useEffect)(() => {
        isMounted.current = true;
        return () => { isMounted.current = false; };
    }, []);
    const execute = (0, react_1.useCallback)((func, val) => __awaiter(this, void 0, void 0, function* () {
        setIsExecuting(true);
        setValue(val);
        try {
            yield func(val);
        }
        catch (err) {
            if (isMounted.current) {
                setValue(initialValue);
            }
            throw err;
        }
        finally {
            if (isMounted.current) {
                setIsExecuting(false);
            }
        }
    }), []);
    return [isExecuting, value, execute];
}
