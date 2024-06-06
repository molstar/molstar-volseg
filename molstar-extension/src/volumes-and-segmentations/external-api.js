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
exports.getPdbIdsForEmdbEntry = exports.tryGetIsovalue = void 0;
const helpers_1 = require("./helpers");
/** Try to get author-defined contour value for isosurface from EMDB API. Return relative value 1.0, if not applicable or fails.  */
function tryGetIsovalue(entryId) {
    return __awaiter(this, void 0, void 0, function* () {
        var _a, _b;
        const split = (0, helpers_1.splitEntryId)(entryId);
        if (split.source === 'emdb') {
            try {
                const response = yield fetch(`https://www.ebi.ac.uk/emdb/api/entry/map/${split.entryNumber}`);
                const json = yield response.json();
                const contours = (_b = (_a = json === null || json === void 0 ? void 0 : json.map) === null || _a === void 0 ? void 0 : _a.contour_list) === null || _b === void 0 ? void 0 : _b.contour;
                if (contours && contours.length > 0) {
                    const theContour = contours.find(c => c.primary) || contours[0];
                    if (theContour.level === undefined)
                        throw new Error('EMDB API response missing contour level.');
                    return { kind: 'absolute', value: theContour.level };
                }
            }
            catch (_c) {
                // do nothing
            }
        }
        return undefined;
    });
}
exports.tryGetIsovalue = tryGetIsovalue;
function getPdbIdsForEmdbEntry(entryId) {
    return __awaiter(this, void 0, void 0, function* () {
        var _a, _b, _c;
        const split = (0, helpers_1.splitEntryId)(entryId);
        const result = [];
        if (split.source === 'emdb') {
            entryId = entryId.toUpperCase();
            const apiUrl = `https://www.ebi.ac.uk/pdbe/api/emdb/entry/fitted/${entryId}`;
            try {
                const response = yield fetch(apiUrl);
                if (response.ok) {
                    const json = yield response.json();
                    const jsonEntry = (_a = json[entryId]) !== null && _a !== void 0 ? _a : [];
                    for (const record of jsonEntry) {
                        const pdbs = (_c = (_b = record === null || record === void 0 ? void 0 : record.fitted_emdb_id_list) === null || _b === void 0 ? void 0 : _b.pdb_id) !== null && _c !== void 0 ? _c : [];
                        result.push(...pdbs);
                    }
                }
            }
            catch (ex) {
                // do nothing
            }
        }
        return result;
    });
}
exports.getPdbIdsForEmdbEntry = getPdbIdsForEmdbEntry;
