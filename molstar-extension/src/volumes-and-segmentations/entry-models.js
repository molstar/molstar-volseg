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
exports.VolsegModelData = void 0;
const data_1 = require("molstar/lib/mol-plugin-state/transforms/data");
const misc_1 = require("molstar/lib/mol-plugin-state/transforms/misc");
const model_1 = require("molstar/lib/mol-plugin-state/transforms/model");
const state_1 = require("molstar/lib/mol-plugin/behavior/static/state");
class VolsegModelData {
    constructor(rootData) {
        this.entryData = rootData;
    }
    loadPdb(pdbId, parent) {
        return __awaiter(this, void 0, void 0, function* () {
            const url = `https://www.ebi.ac.uk/pdbe/entry-files/download/${pdbId}.bcif`;
            const dataNode = yield this.entryData.plugin.build().to(parent).apply(data_1.Download, { url: url, isBinary: true }, { tags: ['fitted-model-data', `pdbid-${pdbId}`] }).commit();
            const cifNode = yield this.entryData.plugin.build().to(dataNode).apply(data_1.ParseCif).commit();
            const trajectoryNode = yield this.entryData.plugin.build().to(cifNode).apply(model_1.TrajectoryFromMmCif).commit();
            yield this.entryData.plugin.builders.structure.hierarchy.applyPreset(trajectoryNode, 'default', { representationPreset: 'polymer-cartoon' });
            return dataNode;
        });
    }
    showPdbs(pdbIds) {
        return __awaiter(this, void 0, void 0, function* () {
            var _a, _b, _c;
            const segmentsToShow = new Set(pdbIds);
            const visuals = this.entryData.findNodesByTags('fitted-model-data');
            for (const visual of visuals) {
                const theTag = (_b = (_a = visual.obj) === null || _a === void 0 ? void 0 : _a.tags) === null || _b === void 0 ? void 0 : _b.find(tag => tag.startsWith('pdbid-'));
                if (!theTag)
                    continue;
                const id = theTag.split('-')[1];
                const visibility = segmentsToShow.has(id);
                (0, state_1.setSubtreeVisibility)(this.entryData.plugin.state.data, visual.transform.ref, !visibility); // true means hide, ¯\_(ツ)_/¯
                segmentsToShow.delete(id);
            }
            const segmentsToCreate = Array.from(segmentsToShow);
            if (segmentsToCreate.length === 0)
                return;
            let group = (_c = this.entryData.findNodesByTags('fitted-models-group')[0]) === null || _c === void 0 ? void 0 : _c.transform.ref;
            if (!group) {
                const newGroupNode = yield this.entryData.newUpdate().apply(misc_1.CreateGroup, { label: 'Fitted Models' }, { tags: ['fitted-models-group'], state: { isCollapsed: true } }).commit();
                group = newGroupNode.ref;
            }
            const awaiting = [];
            for (const pdbId of segmentsToCreate) {
                awaiting.push(this.loadPdb(pdbId, group));
            }
            for (const promise of awaiting)
                yield promise;
        });
    }
}
exports.VolsegModelData = VolsegModelData;
