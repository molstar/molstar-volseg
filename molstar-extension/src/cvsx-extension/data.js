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
exports.CVSXData = void 0;
const common_1 = require("../common");
;
class CVSXData {
    constructor(cvsxFilesIndex, plugin) {
        this.cvsxFilesIndex = cvsxFilesIndex;
        this.plugin = plugin;
    }
    volumeDataFromRaw(rawVolumes) {
        const data = rawVolumes.map(v => {
            const d = {
                channelId: this.cvsxFilesIndex.volumes[v[0]].channelId,
                timeframeIndex: this.cvsxFilesIndex.volumes[v[0]].timeframeIndex,
                data: v[1]
            };
            return d;
        });
        return data;
    }
    latticeSegmentationDataFromRaw(rawData) {
        const l = this.cvsxFilesIndex.latticeSegmentations;
        if (!rawData || !l)
            return undefined;
        const data = rawData.map(v => {
            const d = {
                segmentationId: l[v[0]].segmentationId,
                timeframeIndex: l[v[0]].timeframeIndex,
                data: v[1]
            };
            return d;
        });
        return data;
    }
    meshSegmentationDataFromRaw(rawData) {
        const data = [];
        const meshesInfo = this.cvsxFilesIndex.meshSegmentations;
        if (!rawData || !meshesInfo)
            return undefined;
        for (const m of meshesInfo) {
            const targetSegments = rawData.filter(r => m.segmentsFilenames.includes(r[0]));
            const d = {
                segmentationId: m.segmentationId,
                timeframeIndex: m.timeframeIndex,
                data: targetSegments
            };
            data.push(d);
        }
        return data;
    }
    geometricSegmentationDataFromRaw(rawData) {
        return __awaiter(this, void 0, void 0, function* () {
            const data = [];
            const gsInfo = this.cvsxFilesIndex.geometricSegmentations;
            if (!rawData || !gsInfo)
                return undefined;
            // each key is file name
            for (const gsFileName in gsInfo) {
                // get gsData based on filename
                const gsData = rawData.find(r => r[0] === gsFileName);
                if (!gsData)
                    throw Error('Geometric segmentation file not found');
                const parsedGsData = yield (0, common_1.parseCVSXJSON)(gsData, this.plugin);
                const d = {
                    segmentationId: gsInfo[gsFileName].segmentationId,
                    timeframeIndex: gsInfo[gsFileName].timeframeIndex,
                    data: parsedGsData
                };
                data.push(d);
            }
            return data;
        });
    }
}
exports.CVSXData = CVSXData;
