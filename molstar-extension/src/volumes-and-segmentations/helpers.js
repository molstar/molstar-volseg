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
exports.lazyGetter = exports.applyEllipsis = exports.CreateVolume = exports.CreateTransformer = exports.NodeManager = exports.isDefined = exports.createEntryId = exports.splitEntryId = exports.objectToArray = void 0;
const objects_1 = require("molstar/lib/mol-plugin-state/objects");
const state_1 = require("molstar/lib/mol-plugin/behavior/static/state");
const mol_state_1 = require("molstar/lib/mol-state");
const param_definition_1 = require("molstar/lib/mol-util/param-definition");
function objectToArray(o) {
    if (o) {
        const d = [];
        const arr = Object.entries(o);
        for (const obj of arr) {
            d.push(obj[1]);
        }
        ;
        return d;
    }
    else {
        return [];
    }
}
exports.objectToArray = objectToArray;
/** Split entry ID (e.g. 'emd-1832') into source ('emdb') and number ('1832') */
function splitEntryId(entryId) {
    var _a;
    const PREFIX_TO_SOURCE = { 'emd': 'emdb' };
    const [prefix, entry] = entryId.split('-');
    return {
        source: (_a = PREFIX_TO_SOURCE[prefix]) !== null && _a !== void 0 ? _a : prefix,
        entryNumber: entry
    };
}
exports.splitEntryId = splitEntryId;
/** Create entry ID (e.g. 'emd-1832') for a combination of source ('emdb') and number ('1832') */
function createEntryId(source, entryNumber) {
    var _a;
    const SOURCE_TO_PREFIX = { 'emdb': 'emd' };
    const prefix = (_a = SOURCE_TO_PREFIX[source]) !== null && _a !== void 0 ? _a : source;
    return `${prefix}-${entryNumber}`;
}
exports.createEntryId = createEntryId;
function isDefined(x) {
    return x !== undefined;
}
exports.isDefined = isDefined;
class NodeManager {
    constructor() {
        this.nodes = {};
    }
    static nodeExists(node) {
        try {
            return node.checkValid();
        }
        catch (_a) {
            return false;
        }
    }
    getNode(key) {
        const node = this.nodes[key];
        if (node && !NodeManager.nodeExists(node)) {
            delete this.nodes[key];
            return undefined;
        }
        return node;
    }
    getNodes() {
        return Object.keys(this.nodes).map(key => this.getNode(key)).filter(node => node);
    }
    deleteAllNodes(update) {
        for (const node of this.getNodes()) {
            update.delete(node);
        }
        this.nodes = {};
    }
    hideAllNodes() {
        for (const node of this.getNodes()) {
            (0, state_1.setSubtreeVisibility)(node.state, node.ref, true); // hide
        }
    }
    showNode(key_1, factory_1) {
        return __awaiter(this, arguments, void 0, function* (key, factory, forceVisible = true) {
            let node = this.getNode(key);
            if (node) {
                if (forceVisible) {
                    (0, state_1.setSubtreeVisibility)(node.state, node.ref, false); // show
                }
            }
            else {
                node = yield factory();
                this.nodes[key] = node;
            }
            return node;
        });
    }
}
exports.NodeManager = NodeManager;
exports.CreateTransformer = mol_state_1.StateTransformer.builderFactory('new-volseg');
exports.CreateVolume = (0, exports.CreateTransformer)({
    name: 'new-create-transformer',
    from: objects_1.PluginStateObject.Root,
    to: objects_1.PluginStateObject.Volume.Data,
    params: {
        label: param_definition_1.ParamDefinition.Text('Volume', { isHidden: true }),
        description: param_definition_1.ParamDefinition.Text('', { isHidden: true }),
        volume: param_definition_1.ParamDefinition.Value(undefined, { isHidden: true }),
    }
})({
    apply({ params }) {
        return new objects_1.PluginStateObject.Volume.Data(params.volume, { label: params.label, description: params.description });
    }
});
function applyEllipsis(name, max_chars = 60) {
    if (name.length <= max_chars)
        return name;
    const beginning = name.substring(0, max_chars);
    let lastSpace = beginning.lastIndexOf(' ');
    if (lastSpace === -1)
        return beginning + '...';
    if (lastSpace > 0 && ',;.'.includes(name.charAt(lastSpace - 1)))
        lastSpace--;
    return name.substring(0, lastSpace) + '...';
}
exports.applyEllipsis = applyEllipsis;
function lazyGetter(getter, errorIfUndefined) {
    let value = undefined;
    return () => {
        if (value === undefined)
            value = getter();
        if (errorIfUndefined && value === undefined)
            throw new Error(errorIfUndefined);
        return value;
    };
}
exports.lazyGetter = lazyGetter;
