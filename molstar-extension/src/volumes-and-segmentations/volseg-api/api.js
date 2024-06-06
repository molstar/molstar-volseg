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
exports.VolumeApiV2 = exports.DEFAULT_VOLSEG_SERVER = void 0;
exports.DEFAULT_VOLSEG_SERVER = 'https://molstarvolseg.ncbr.muni.cz/v2';
class VolumeApiV2 {
    constructor(volumeServerUrl = exports.DEFAULT_VOLSEG_SERVER) {
        this.volumeServerUrl = volumeServerUrl.replace(/\/$/, ''); // trim trailing slash
    }
    updateAnnotationsJson(source, entryId, annotationsJson) {
        return __awaiter(this, void 0, void 0, function* () {
            const url = `${this.volumeServerUrl}/${source}/${entryId}/annotations_json/update`;
            const obj = JSON.stringify({ annotations_json: annotationsJson });
            yield fetch(url, {
                method: 'POST',
                body: obj,
                headers: { 'Content-Type': 'application/json' }
            });
        });
    }
    editDescriptionsUrl(source, entryId, descriptionData) {
        return __awaiter(this, void 0, void 0, function* () {
            const url = `${this.volumeServerUrl}/${source}/${entryId}/descriptions/edit`;
            const obj = JSON.stringify({ descriptions: descriptionData });
            yield fetch(url, {
                method: 'POST',
                body: obj,
                headers: { 'Content-Type': 'application/json' }
            });
        });
    }
    editSegmentAnnotationsUrl(source, entryId, segmentAnnotationData) {
        return __awaiter(this, void 0, void 0, function* () {
            const url = `${this.volumeServerUrl}/${source}/${entryId}/segment_annotations/edit`;
            const obj = JSON.stringify({ segment_annotations: segmentAnnotationData });
            yield fetch(url, {
                method: 'POST',
                body: obj,
                headers: { 'Content-Type': 'application/json' }
            });
        });
    }
    removeDescriptionsUrl(source, entryId, description_ids) {
        return __awaiter(this, void 0, void 0, function* () {
            const url = `${this.volumeServerUrl}/${source}/${entryId}/descriptions/remove`;
            const obj = JSON.stringify({ description_ids: description_ids });
            yield fetch(url, {
                method: 'POST',
                body: obj,
                headers: { 'Content-Type': 'application/json' }
            });
        });
    }
    removeSegmentAnnotationsUrl(source, entryId, annotation_ids) {
        return __awaiter(this, void 0, void 0, function* () {
            const url = `${this.volumeServerUrl}/${source}/${entryId}/segment_annotations/remove`;
            const obj = JSON.stringify({ annotation_ids: annotation_ids });
            yield fetch(url, {
                method: 'POST',
                body: obj,
                headers: { 'Content-Type': 'application/json' }
            });
        });
    }
    entryListUrl(maxEntries, keyword) {
        return `${this.volumeServerUrl}/list_entries/${maxEntries}/${keyword !== null && keyword !== void 0 ? keyword : ''}`;
    }
    metadataUrl(source, entryId) {
        return `${this.volumeServerUrl}/${source}/${entryId}/metadata`;
    }
    volumeUrl(source, entryId, timeframe, channelId, box, maxPoints) {
        if (box) {
            const [[a1, a2, a3], [b1, b2, b3]] = box;
            return `${this.volumeServerUrl}/${source}/${entryId}/volume/box/${timeframe}/${channelId}/${a1}/${a2}/${a3}/${b1}/${b2}/${b3}?max_points=${maxPoints}`;
        }
        else {
            return `${this.volumeServerUrl}/${source}/${entryId}/volume/cell/${timeframe}/${channelId}?max_points=${maxPoints}`;
        }
    }
    latticeUrl(source, entryId, segmentation, timeframe, box, maxPoints) {
        if (box) {
            const [[a1, a2, a3], [b1, b2, b3]] = box;
            return `${this.volumeServerUrl}/${source}/${entryId}/segmentation/box/${segmentation}/${timeframe}/${a1}/${a2}/${a3}/${b1}/${b2}/${b3}?max_points=${maxPoints}`;
        }
        else {
            return `${this.volumeServerUrl}/${source}/${entryId}/segmentation/cell/${segmentation}/${timeframe}?max_points=${maxPoints}`;
        }
    }
    geometricSegmentationUrl(source, entryId, segmentation_id, timeframe) {
        return `${this.volumeServerUrl}/${source}/${entryId}/geometric_segmentation/${segmentation_id}/${timeframe}`;
    }
    meshUrl_Json(source, entryId, segmentation_id, timeframe, segment, detailLevel) {
        return `${this.volumeServerUrl}/${source}/${entryId}/mesh/${segmentation_id}/${timeframe}/${segment}/${detailLevel}`;
    }
    meshUrl_Bcif(source, entryId, segmentation_id, timeframe, segment, detailLevel) {
        return `${this.volumeServerUrl}/${source}/${entryId}/mesh_bcif/${segmentation_id}/${timeframe}/${segment}/${detailLevel}`;
    }
    volumeInfoUrl(source, entryId) {
        return `${this.volumeServerUrl}/${source}/${entryId}/volume_info`;
    }
    getEntryList(maxEntries, keyword) {
        return __awaiter(this, void 0, void 0, function* () {
            const response = yield fetch(this.entryListUrl(maxEntries, keyword));
            return yield response.json();
        });
    }
    getMetadata(source, entryId) {
        return __awaiter(this, void 0, void 0, function* () {
            const url = this.metadataUrl(source, entryId);
            const response = yield fetch(url);
            if (!response.ok)
                throw new Error(`Failed to fetch metadata from ${url}`);
            return yield response.json();
        });
    }
}
exports.VolumeApiV2 = VolumeApiV2;
