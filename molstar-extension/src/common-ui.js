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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.SelectedSegmentDescription = exports.DescriptionsList = exports.DescriptionsListItem = exports.MetadataTextFilter = exports.EntryDescriptionUI = exports.ExternalReferencesUI = exports.DescriptionTextUI = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */
const common_1 = require("molstar/lib/mol-plugin-ui/controls/common");
const sleep_1 = require("molstar/lib/mol-util/sleep");
const common_2 = require("./common");
const ui_1 = require("./volumes-and-segmentations/ui");
const utils_1 = require("./volumes-and-segmentations/volseg-api/utils");
const Icons = __importStar(require("molstar/lib/mol-plugin-ui/controls/icons"));
const use_behavior_1 = require("molstar/lib/mol-plugin-ui/hooks/use-behavior");
const react_markdown_1 = __importDefault(require("react-markdown"));
const string_1 = require("molstar/lib/mol-util/string");
const react_1 = require("react");
function DescriptionTextUI({ descriptionText: d }) {
    if (d.format === 'markdown') {
        return (0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)("br", {}), (0, jsx_runtime_1.jsx)("br", {}), (0, jsx_runtime_1.jsx)("b", { children: "Description: " }), (0, jsx_runtime_1.jsx)(react_markdown_1.default, { skipHtml: true, children: d.text })] });
    }
    else if (d.format === 'text') {
        return (0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)("br", {}), (0, jsx_runtime_1.jsx)("br", {}), (0, jsx_runtime_1.jsx)("b", { children: "Description: " }), (0, jsx_runtime_1.jsx)("p", { children: d.text })] });
    }
}
exports.DescriptionTextUI = DescriptionTextUI;
// Renders all external references
function ExternalReferencesUI({ externalReferences: e }) {
    return (0, jsx_runtime_1.jsx)(jsx_runtime_1.Fragment, { children: e.map(ref => {
            return (0, jsx_runtime_1.jsxs)("p", { style: { marginTop: 4 }, children: [ref.url ? (0, jsx_runtime_1.jsxs)("a", { href: ref.url, children: [ref.resource, ":", ref.accession] }) :
                        (0, jsx_runtime_1.jsxs)("small", { children: [ref.resource, ":", ref.accession] }), (0, jsx_runtime_1.jsx)("br", {}), (0, jsx_runtime_1.jsx)("b", { children: (0, string_1.capitalize)(ref.label ? ref.label : '') }), (0, jsx_runtime_1.jsx)("br", {}), ref.description] }, ref.id);
        }) });
}
exports.ExternalReferencesUI = ExternalReferencesUI;
function EntryDescriptionUI({ entryDescriptionData: e }) {
    var _a;
    return (0, jsx_runtime_1.jsx)(common_1.ExpandGroup, { header: 'Entry description data', children: (0, jsx_runtime_1.jsxs)("div", { children: [(_a = e.name) !== null && _a !== void 0 ? _a : '', e.details && (0, jsx_runtime_1.jsx)(DescriptionTextUI, { descriptionText: e.details }), e.external_references && (0, jsx_runtime_1.jsx)(ExternalReferencesUI, { externalReferences: e.external_references })] }, e.id) });
}
exports.EntryDescriptionUI = EntryDescriptionUI;
const MetadataTextFilter = ({ setFilteredDescriptions, descriptions, model }) => {
    const [text, setText] = (0, react_1.useState)('');
    function filterDescriptions(keyword) {
        return model.metadata.value.filterDescriptions(descriptions, keyword);
    }
    return ((0, jsx_runtime_1.jsx)(common_1.TextInput, { style: { order: 1, flex: '1 1 auto', minWidth: 0, marginBlock: 1 }, className: 'msp-form-control', value: text, placeholder: "Type keyword to filter segments...", onChange: newText => {
            setText(newText);
            const filteredDescriptions = filterDescriptions(newText);
            setFilteredDescriptions(filteredDescriptions);
        } }));
};
exports.MetadataTextFilter = MetadataTextFilter;
function DescriptionsListItem({ model, d, currentTimeframe, selectedSegmentDescription, visibleSegmentKeys }) {
    var _a, _b, _c, _d, _e, _f, _g;
    const metadata = (0, use_behavior_1.useBehavior)(model.metadata);
    if (d.target_kind === 'entry' || !d.target_id || d.is_hidden === true)
        return;
    // NOTE: if time is a single number
    if (d.time && Number.isFinite(d.time) && d.time !== currentTimeframe)
        return;
    // NOTE: if time is array
    if (d.time && Array.isArray(d.time) && d.time.every(i => Number.isFinite(i)) && !d.time.includes(currentTimeframe))
        return;
    const segmentKey = (0, utils_1.createSegmentKey)(d.target_id.segment_id, d.target_id.segmentation_id, d.target_kind);
    const targetDescriptionCurrent = metadata.raw.annotation.descriptions[d.id];
    d = targetDescriptionCurrent;
    if (d.target_kind === 'entry' || !d.target_id || d.is_hidden === true)
        return;
    return (0, jsx_runtime_1.jsxs)("div", { className: 'msp-flex-row', style: { marginTop: '1px' }, children: [(0, jsx_runtime_1.jsx)(common_1.Button, { noOverflow: true, flex: true, onClick: () => (0, common_2.actionSelectSegment)(model, d !== selectedSegmentDescription ? segmentKey : undefined), style: {
                    fontWeight: d.target_id.segment_id === ((_a = selectedSegmentDescription === null || selectedSegmentDescription === void 0 ? void 0 : selectedSegmentDescription.target_id) === null || _a === void 0 ? void 0 : _a.segment_id)
                        && d.target_id.segmentation_id === (selectedSegmentDescription === null || selectedSegmentDescription === void 0 ? void 0 : selectedSegmentDescription.target_id.segmentation_id)
                        ? 'bold' : undefined, textAlign: 'left'
                }, children: (0, jsx_runtime_1.jsxs)("div", { title: (_b = d.name) !== null && _b !== void 0 ? _b : 'Unnamed segment', style: { maxWidth: 240, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }, children: [(_c = d.name) !== null && _c !== void 0 ? _c : 'Unnamed segment', " (", (_d = d.target_id) === null || _d === void 0 ? void 0 : _d.segment_id, ") (", (_e = d.target_id) === null || _e === void 0 ? void 0 : _e.segmentation_id, ")"] }) }), (0, jsx_runtime_1.jsx)(common_1.IconButton, { svg: visibleSegmentKeys.includes(segmentKey) ? Icons.VisibilityOutlinedSvg : Icons.VisibilityOffOutlinedSvg, title: visibleSegmentKeys.includes(segmentKey) ? 'Hide segment' : 'Show segment', onClick: () => (0, common_2.actionToggleSegment)(model, segmentKey) })] }, `${(_f = d.target_id) === null || _f === void 0 ? void 0 : _f.segment_id}:${(_g = d.target_id) === null || _g === void 0 ? void 0 : _g.segmentation_id}:${d.target_kind}`);
}
exports.DescriptionsListItem = DescriptionsListItem;
function DescriptionsList({ model, targetSegmentationId, targetKind }) {
    const state = (0, use_behavior_1.useBehavior)(model.currentState);
    const currentTimeframe = (0, use_behavior_1.useBehavior)(model.currentTimeframe);
    const metadata = (0, use_behavior_1.useBehavior)(model.metadata);
    const allDescriptionsForSegmentationId = metadata.getDescriptions(targetSegmentationId, targetKind, currentTimeframe);
    const [filteredDescriptions, setFilteredDescriptions] = (0, react_1.useState)(allDescriptionsForSegmentationId);
    const parsedSelectedSegmentKey = (0, utils_1.parseSegmentKey)(state.selectedSegment);
    const { segmentId, segmentationId, kind } = parsedSelectedSegmentKey;
    const selectedSegmentDescriptions = model.metadata.value.getSegmentDescription(segmentId, segmentationId, kind);
    // NOTE: for now single description
    const selectedSegmentDescription = selectedSegmentDescriptions ? selectedSegmentDescriptions[0] : undefined;
    const visibleSegmentKeys = state.visibleSegments.map(seg => seg.segmentKey);
    return (0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)(exports.MetadataTextFilter, { setFilteredDescriptions: setFilteredDescriptions, descriptions: allDescriptionsForSegmentationId, model: model }), filteredDescriptions.length > 0 && (0, jsx_runtime_1.jsxs)("div", { children: [(0, jsx_runtime_1.jsx)(ui_1.WaitingButton, { onClick: () => __awaiter(this, void 0, void 0, function* () { yield (0, sleep_1.sleep)(20); yield (0, common_2.actionToggleAllFilteredSegments)(model, targetSegmentationId, targetKind, filteredDescriptions); }), style: { marginTop: 1 }, children: "Toggle All segments" }), (0, jsx_runtime_1.jsx)("div", { style: { maxHeight: 200, overflow: 'hidden', overflowY: 'auto', marginBlock: 1 }, children: filteredDescriptions.map(d => {
                            return (0, jsx_runtime_1.jsx)(DescriptionsListItem, { model: model, d: d, currentTimeframe: currentTimeframe, selectedSegmentDescription: selectedSegmentDescription, visibleSegmentKeys: visibleSegmentKeys }, d.id);
                        }) })] }, targetSegmentationId)] });
}
exports.DescriptionsList = DescriptionsList;
function SelectedSegmentDescription({ model, targetSegmentationId, targetKind }) {
    var _a;
    const state = (0, use_behavior_1.useBehavior)(model.currentState);
    (0, use_behavior_1.useBehavior)(model.currentTimeframe);
    const metadata = (0, use_behavior_1.useBehavior)(model.metadata);
    const anyDescriptions = metadata.allDescriptions.length > 0;
    const parsedSelectedSegmentKey = (0, utils_1.parseSegmentKey)(state.selectedSegment);
    const { segmentId, segmentationId, kind } = parsedSelectedSegmentKey;
    const selectedSegmentDescriptions = model.metadata.value.getSegmentDescription(segmentId, segmentationId, kind);
    // NOTE: for now single description
    const selectedSegmentDescription = selectedSegmentDescriptions ? selectedSegmentDescriptions[0] : undefined;
    return (0, jsx_runtime_1.jsx)(jsx_runtime_1.Fragment, { children: anyDescriptions && (0, jsx_runtime_1.jsx)(common_1.ExpandGroup, { header: 'Selected segment descriptions', initiallyExpanded: true, children: (0, jsx_runtime_1.jsxs)("div", { style: { paddingTop: 4, paddingRight: 8, maxHeight: 300, overflow: 'hidden', overflowY: 'auto' }, children: [!selectedSegmentDescription && 'No segment selected', selectedSegmentDescription &&
                        selectedSegmentDescription.target_kind !== 'entry' &&
                        selectedSegmentDescription.target_id &&
                        (0, jsx_runtime_1.jsxs)("b", { children: ["Segment ", selectedSegmentDescription.target_id.segment_id, " from segmentation ", selectedSegmentDescription.target_id.segmentation_id, ":", (0, jsx_runtime_1.jsx)("br", {}), (_a = selectedSegmentDescription.name) !== null && _a !== void 0 ? _a : 'Unnamed segment'] }), selectedSegmentDescription && selectedSegmentDescription.details &&
                        (0, jsx_runtime_1.jsx)(DescriptionTextUI, { descriptionText: selectedSegmentDescription.details }), (selectedSegmentDescription === null || selectedSegmentDescription === void 0 ? void 0 : selectedSegmentDescription.external_references) &&
                        (0, jsx_runtime_1.jsx)(ExternalReferencesUI, { externalReferences: selectedSegmentDescription.external_references })] }) }) });
}
exports.SelectedSegmentDescription = SelectedSegmentDescription;
