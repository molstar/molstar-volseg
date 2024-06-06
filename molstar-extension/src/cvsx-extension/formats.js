"use strict";
/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
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
exports.CVSXFormatProvider = void 0;
const _1 = require(".");
const provider_1 = require("molstar/lib/mol-plugin-state/formats/provider");
/** Data format provider for CVSX format.
 */
// StateObjectRef is just a union type which is either the StateObjectSelector | StateObjectCell | StateTranform.Ref (str)
exports.CVSXFormatProvider = (0, provider_1.DataFormatProvider)({
    label: 'CVSX',
    description: 'CVSX',
    category: 'Miscellaneous',
    binaryExtensions: ['cvsx'],
    parse: (plugin, data) => __awaiter(void 0, void 0, void 0, function* () {
        return (0, _1.loadCVSXFromAnything)(plugin, data);
    }),
});
