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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.JSONEditorComponent = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */
const react_1 = require("react");
const jsoneditor_1 = __importDefault(require("jsoneditor"));
require("jsoneditor/dist/jsoneditor.css");
const common_1 = require("molstar/lib/mol-plugin-ui/controls/common");
function updateJSON(jsonData, entryData) {
    return __awaiter(this, void 0, void 0, function* () {
        yield entryData.api.updateAnnotationsJson(entryData.source, entryData.entryId, jsonData);
        yield entryData.updateMetadata();
    });
}
const JSONEditorComponent = ({ jsonData, entryData }) => {
    const containerRef = (0, react_1.useRef)(null);
    let jsonEditor = null;
    const jsonDataUpdated = (0, react_1.useRef)(jsonData);
    (0, react_1.useEffect)(() => {
        if (containerRef.current) {
            const options = {
                onChangeJSON: (jsonData) => __awaiter(void 0, void 0, void 0, function* () {
                    jsonDataUpdated.current = jsonData;
                })
            };
            jsonEditor = new jsoneditor_1.default(containerRef.current, options);
            jsonEditor.set(jsonData);
        }
        return () => {
            if (jsonEditor) {
                jsonEditor.destroy();
            }
        };
    }, [jsonData]);
    return ((0, jsx_runtime_1.jsxs)("div", { style: { flex: '1', flexDirection: 'column' }, children: [(0, jsx_runtime_1.jsx)("div", { ref: containerRef, style: { width: '100%', height: '400px' } }), (0, jsx_runtime_1.jsx)(common_1.Button, { onClick: () => __awaiter(void 0, void 0, void 0, function* () { return yield updateJSON(jsonDataUpdated.current, entryData); }), children: "Update annotations.json" })] }));
};
exports.JSONEditorComponent = JSONEditorComponent;
