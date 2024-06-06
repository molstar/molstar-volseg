"use strict";
/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Adam Midlik <midlik@gmail.com>
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.getSegmentLabelsFromDescriptions = exports.parseSegmentKey = exports.createSegmentKey = exports.instanceOfShapePrimitiveData = exports.MetadataWrapper = exports.compareTwoObjects = void 0;
const color_1 = require("molstar/lib/mol-util/color");
const helpers_1 = require("../helpers");
function compareTwoObjects(object1, object2) {
    if (!object1 || !object2)
        return false;
    let compareRes = true;
    if (Object.keys(object1).length === Object.keys(object2).length) {
        Object.keys(object1).forEach(key => {
            if (object1[key] !== object2[key]) {
                compareRes = false;
            }
        });
    }
    else {
        compareRes = false;
    }
    return compareRes;
}
exports.compareTwoObjects = compareTwoObjects;
class MetadataWrapper {
    constructor(rawMetadata) {
        this.raw = rawMetadata;
    }
    setCurrentlyUsedVolumeDownsampling(n) {
        this.currentlyUsedVolumeDownsampling = n;
    }
    get currentVolumeDownsampling() {
        if (this.currentlyUsedVolumeDownsampling)
            return this.currentlyUsedVolumeDownsampling;
        throw Error('Currently used volume downsampling is not set');
    }
    hasLatticeSegmentations() {
        const grid = this.raw.grid;
        if (grid.segmentation_lattices && grid.segmentation_lattices.segmentation_ids.length > 0) {
            return grid.segmentation_lattices;
        }
        return false;
    }
    ;
    hasMeshSegmentations() {
        const grid = this.raw.grid;
        if (grid.segmentation_meshes && grid.segmentation_meshes.segmentation_ids.length > 0) {
            return grid.segmentation_meshes;
        }
        return false;
    }
    ;
    hasGeometricSegmentations() {
        const grid = this.raw.grid;
        if (grid.geometric_segmentation && grid.geometric_segmentation.segmentation_ids.length > 0) {
            return grid.geometric_segmentation;
        }
        return false;
    }
    ;
    hasSegmentations() {
        const grid = this.raw.grid;
        if (grid.geometric_segmentation && grid.geometric_segmentation.segmentation_ids.length > 0) {
            return true;
        }
        if (grid.segmentation_lattices && grid.segmentation_lattices.segmentation_ids.length > 0) {
            return true;
        }
        if (grid.segmentation_meshes && grid.segmentation_meshes.segmentation_ids.length > 0) {
            return true;
        }
        return false;
    }
    removeDescription(id) {
        var _a;
        const descriptions = (_a = this.raw.annotation) === null || _a === void 0 ? void 0 : _a.descriptions;
        if (this.raw.annotation && descriptions) {
            // const removed = descriptions.filter(d => d.i)
            delete descriptions[id];
            this.raw.annotation.descriptions = descriptions;
        }
    }
    removeSegmentAnnotation(id) {
        const segmentAnnotations = this.allAnnotations;
        const filtered = segmentAnnotations.filter(a => a.id !== id);
        this.raw.annotation.segment_annotations = filtered;
    }
    get allDescriptions() {
        var _a;
        const descriptions = (_a = this.raw.annotation) === null || _a === void 0 ? void 0 : _a.descriptions;
        if (descriptions) {
            return (0, helpers_1.objectToArray)(descriptions);
        }
        else {
            return [];
        }
    }
    getDescriptions(segmentationId, kind, timeframeIndex) {
        const allDescriptions = this.allDescriptions;
        const allDescriptonsForSegmentationId = allDescriptions.filter(d => d.target_id && d.target_id.segmentation_id === segmentationId && d.target_kind === kind);
        const allDescriptonsForSegmentationIdAndTimeframe = allDescriptonsForSegmentationId.filter(a => {
            if (a.hasOwnProperty('time') && Number.isFinite(a.time)) {
                if (timeframeIndex === a.time) {
                    return a;
                }
            }
            else if (a.hasOwnProperty('time') && Array.isArray(a.time) && a.time.every(i => Number.isFinite(i))) {
                if (a.time.includes(timeframeIndex)) {
                    return a;
                }
            }
            else {
                return a;
            }
        });
        return allDescriptonsForSegmentationIdAndTimeframe;
    }
    get allAnnotations() {
        var _a;
        const annotations = (_a = this.raw.annotation) === null || _a === void 0 ? void 0 : _a.segment_annotations;
        if (annotations)
            return annotations;
        else
            return [];
    }
    getAllAnnotations(timeframeIndex) {
        const allSegmentsForTimeframe = this.allAnnotations.filter(a => {
            if (a.hasOwnProperty('time') && Number.isFinite(a.time)) {
                if (timeframeIndex === a.time) {
                    return a;
                }
            }
            else if (a.hasOwnProperty('time') && Array.isArray(a.time) && a.time.every(i => Number.isFinite(i))) {
                if (a.time.includes(timeframeIndex)) {
                    return a;
                }
            }
            else {
                return a;
            }
        });
        return allSegmentsForTimeframe;
    }
    get allSegmentIds() {
        var _a;
        return (_a = this.allAnnotations) === null || _a === void 0 ? void 0 : _a.map(annotation => annotation.segment_id);
    }
    get channelAnnotations() {
        var _a;
        return (_a = this.raw.annotation) === null || _a === void 0 ? void 0 : _a.volume_channels_annotations;
    }
    getVolumeChannelColor(channel_id) {
        var _a;
        if (!this.channelAnnotations) {
            return (0, color_1.Color)(0x121212);
        }
        const channelColorArray = (_a = this.channelAnnotations.filter(i => i.label === channel_id)[0]) === null || _a === void 0 ? void 0 : _a.color;
        if (channelColorArray) {
            const color = color_1.Color.fromNormalizedArray(channelColorArray, 0);
            return color;
        }
        else {
            return (0, color_1.Color)(0x121212);
        }
    }
    getVolumeChannelLabel(channel_id) {
        var _a;
        if (!this.channelAnnotations) {
            return null;
        }
        const volumeChannelLabel = (_a = this.channelAnnotations
            .filter(i => i.channel_id === channel_id)[0]) === null || _a === void 0 ? void 0 : _a.label;
        if (volumeChannelLabel) {
            return volumeChannelLabel;
        }
        else {
            return null;
        }
        ;
    }
    getSegmentAnnotation(segmentId, segmentationId, kind) {
        const allAnnotations = this.allAnnotations;
        return allAnnotations.find(a => a.segment_id === segmentId && a.segment_kind === kind && a.segmentation_id === segmentationId);
    }
    getSegmentDescription(segmentId, segmentationId, kind) {
        const segmentKey = createSegmentKey(segmentId, segmentationId, kind);
        if (this.allDescriptions) {
            // create segment map
            if (!this.segmentMap) {
                this.segmentMap = new Map;
                for (const description of this.allDescriptions) {
                    if (description.target_id && description.target_kind !== 'entry') {
                        const _kind = description.target_kind;
                        const _segmentationId = description.target_id.segmentation_id;
                        const _segmentId = description.target_id.segment_id;
                        const _segmentKey = createSegmentKey(_segmentId, _segmentationId, _kind);
                        const existingDescriptions = this.segmentMap.get(_segmentKey);
                        if (existingDescriptions) {
                            this.segmentMap.set(_segmentKey, [...existingDescriptions, description]);
                        }
                        else {
                            this.segmentMap.set(_segmentKey, [description]);
                        }
                    }
                }
            }
            return this.segmentMap.get(segmentKey);
        }
    }
    /** Get the list of detail levels available for the given mesh segment. */
    getMeshDetailLevels(segmentationId, timeframe, segmentId) {
        if (!this.raw.grid.segmentation_meshes)
            return [];
        const meshComponentNumbers = this.raw.grid.segmentation_meshes.segmentation_metadata[segmentationId].mesh_timeframes[timeframe];
        // const segmentIds = segmentationSetMetadata.
        const segmentIds = meshComponentNumbers.segment_ids;
        if (!segmentIds)
            return [];
        const details = segmentIds[segmentId].detail_lvls;
        return Object.keys(details).map(s => parseInt(s));
        // const segmentIds = this.raw.grid.segmentation_meshes.mesh_component_numbers.segment_ids;
        // if (!segmentIds) return [];
        // const details = segmentIds[segmentId].detail_lvls;
        // return Object.keys(details).map(s => parseInt(s));
    }
    /** Get the worst available detail level that is not worse than preferredDetail.
     * If preferredDetail is null, get the worst detail level overall.
     * (worse = greater number) */
    getSufficientMeshDetail(segmentationId, timeframe, segmentId, preferredDetail) {
        let availDetails = this.getMeshDetailLevels(segmentationId, timeframe, segmentId);
        if (preferredDetail !== null) {
            availDetails = availDetails.filter(det => det <= preferredDetail);
        }
        return Math.max(...availDetails);
    }
    /** IDs of all segments available as meshes */
    // make it work for multiple mesh sets?
    getMeshSegmentIdsForSegmentationIdAndTimeframe(segmentationId, timeframe) {
        // if (!this.raw.grid.segmentation_meshes) return;
        const meshComponentNumbers = this.raw.grid.segmentation_meshes.segmentation_metadata[segmentationId].mesh_timeframes[timeframe];
        // const segmentIds = segmentationSetMetadata.
        const segmentIds = meshComponentNumbers.segment_ids;
        if (!segmentIds)
            return [];
        return Object.keys(segmentIds).map(s => parseInt(s));
    }
    getAllDescriptionsBasedOnMetadata(metadata) {
        const a = this.allDescriptions;
        const filtered = a.filter(i => compareTwoObjects(i.metadata, metadata));
        return filtered;
    }
    filterDescriptions(d, keyword) {
        if (keyword === '')
            return d;
        const kw = keyword.toLowerCase();
        const filtered = d.filter(i => {
            if (i.name) {
                if (i.name.toLowerCase().includes(kw)) {
                    return true;
                }
            }
            if (i.metadata) {
                const values = Object.values(i.metadata);
                const valuesLowerCase = values.map(v => v.toLowerCase());
                if (valuesLowerCase.includes(kw))
                    return true;
            }
        });
        return filtered;
    }
    getAllSegmentAnotationsForSegmentationAndTimeframe(segmentationId, kind, timeframeIndex) {
        const allAnnotations = this.allAnnotations;
        const allAnnotationsForSegmentationId = allAnnotations.filter(d => d.segmentation_id === segmentationId && d.segment_kind === kind);
        const allAnnotationsForSegmentationIdAndTimeframe = allAnnotationsForSegmentationId.filter(a => {
            if (a.hasOwnProperty('time') && Number.isFinite(a.time)) {
                if (timeframeIndex === a.time) {
                    return a;
                }
            }
            else if (a.hasOwnProperty('time') && Array.isArray(a.time) && a.time.every(i => Number.isFinite(i))) {
                if (a.time.includes(timeframeIndex)) {
                    return a;
                }
            }
            else {
                return a;
            }
        });
        return allAnnotationsForSegmentationIdAndTimeframe;
    }
    get gridTotalVolume() {
        const currentVolumeDownsampling = this.currentVolumeDownsampling;
        const [vx, vy, vz] = this.raw.grid.volumes.volume_sampling_info.boxes[currentVolumeDownsampling].voxel_size;
        const [gx, gy, gz] = this.raw.grid.volumes.volume_sampling_info.boxes[currentVolumeDownsampling].grid_dimensions;
        return vx * vy * vz * gx * gy * gz;
    }
}
exports.MetadataWrapper = MetadataWrapper;
function instanceOfShapePrimitiveData(object) {
    return 'shape_primitive_list' in object;
}
exports.instanceOfShapePrimitiveData = instanceOfShapePrimitiveData;
function createSegmentKey(segmentId, segmentationId, kind) {
    return `${kind}:${segmentationId}:${segmentId}`;
}
exports.createSegmentKey = createSegmentKey;
function parseSegmentKey(segmentKey) {
    const kind = segmentKey.split(':')[0];
    const segmentationId = segmentKey.split(':')[1];
    const segmentId = segmentKey.split(':')[2];
    const parsedSegmentKey = {
        kind: kind,
        segmentationId: segmentationId,
        segmentId: Number(segmentId)
    };
    return parsedSegmentKey;
}
exports.parseSegmentKey = parseSegmentKey;
function getSegmentLabelsFromDescriptions(descriptions) {
    return descriptions.map(description => ({ id: description.target_id.segment_id, label: (description === null || description === void 0 ? void 0 : description.name) && !(description === null || description === void 0 ? void 0 : description.is_hidden) ? `<b>${description === null || description === void 0 ? void 0 : description.name}</b>` : 'No label provided or description is hidden' }));
}
exports.getSegmentLabelsFromDescriptions = getSegmentLabelsFromDescriptions;
