/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */

import { PluginContext } from 'molstar/lib/mol-plugin/context';
import { Source, parseCVSXJSON } from '../src/common';
import { AnnotationMetadata, GridMetadata, ShapePrimitiveData } from '../volumes-and-segmentations/volseg-api/data';

export interface CVSXFilesData {
    volumes?: CVSXVolumeData[]
    latticeSegmentations?: CVSXLatticeSegmentationData[],
    geometricSegmentations?: CVSXGeometricSegmentationData[],
    meshSegmentations?: CVSXMeshSegmentationData[],
    annotations?: AnnotationMetadata,
    metadata?: GridMetadata,
    query: QueryArgs,
    index: CVSXFilesIndex
};

export interface CVSXFileInfo {
    type: 'volume' | 'lattice' | 'mesh' | 'geometric-segmentation' | 'annotations' | 'metadata' | 'query'
}

export interface VolumeFileInfo extends CVSXFileInfo {
    channelId: string
    timeframeIndex: number
}

export interface SegmentationFileInfo extends CVSXFileInfo {
    segmentationId: string
    timeframeIndex: number
}
export interface LatticeSegmentationFileInfo extends SegmentationFileInfo {

}

export interface MeshSegmentationFilesInfo extends SegmentationFileInfo {
    segmentsFilenames: string[]
}

export interface GeometricSegmentationFileInfo extends SegmentationFileInfo {

}

export interface CVSXFilesIndex {
    // file name to info mapping
    volumes: { [filename: string]: VolumeFileInfo }
    // file name to info mapping
    latticeSegmentations?: { [filename: string]: LatticeSegmentationFileInfo }
    // file name to info mapping
    geometricSegmentations?: { [filename: string]: GeometricSegmentationFileInfo }
    meshSegmentations?: MeshSegmentationFilesInfo[]
    // file names
    annotations: string
    metadata: string
    query: string
}
export interface CVSXGeometricSegmentationData {
    segmentationId: string
    timeframeIndex: number
    data: ShapePrimitiveData
}

export interface CVSXMeshSegmentationData {
    segmentationId: string
    timeframeIndex: number
    // segment id, segment data
    data: [string, Uint8Array][]
}

export class CVSXData {
    constructor(public cvsxFilesIndex: CVSXFilesIndex, public plugin: PluginContext) {
    }

    volumeDataFromRaw(rawVolumes: [string, Uint8Array][]) {
        const data = rawVolumes.map(v => {
            const d: CVSXVolumeData = {
                channelId: this.cvsxFilesIndex.volumes[v[0]].channelId,
                timeframeIndex: this.cvsxFilesIndex.volumes[v[0]].timeframeIndex,
                data: v[1]
            };
            return d;
        });
        return data;
    }

    latticeSegmentationDataFromRaw(rawData?: [string, Uint8Array][]) {
        const l = this.cvsxFilesIndex.latticeSegmentations;
        if (!rawData || !l) return undefined;
        const data = rawData.map(v => {
            const d: CVSXLatticeSegmentationData = {
                segmentationId: l[v[0]].segmentationId,
                timeframeIndex: l[v[0]].timeframeIndex,
                data: v[1]
            };
            return d;
        });
        return data;
    }

    meshSegmentationDataFromRaw(rawData?: [string, Uint8Array][]) {
        const data: CVSXMeshSegmentationData[] = [];
        const meshesInfo = this.cvsxFilesIndex.meshSegmentations;
        if (!rawData || !meshesInfo) return undefined;
        for (const m of meshesInfo) {
            const targetSegments = rawData.filter(r => m.segmentsFilenames.includes(r[0]));
            const d: CVSXMeshSegmentationData = {
                segmentationId: m.segmentationId,
                timeframeIndex: m.timeframeIndex,
                data: targetSegments
            };
            data.push(d);
        }
        return data;
    }

    async geometricSegmentationDataFromRaw(rawData?: [string, Uint8Array][]) {
        const data: CVSXGeometricSegmentationData[] = [];
        const gsInfo = this.cvsxFilesIndex.geometricSegmentations;
        if (!rawData || !gsInfo) return undefined;
        // each key is file name
        for (const gsFileName in gsInfo) {
            // get gsData based on filename
            const gsData = rawData.find(r => r[0] === gsFileName);
            if (!gsData) throw Error('Geometric segmentation file not found');
            const parsedGsData: ShapePrimitiveData = await parseCVSXJSON(gsData, this.plugin);
            const d: CVSXGeometricSegmentationData = {
                segmentationId: gsInfo[gsFileName].segmentationId,
                timeframeIndex: gsInfo[gsFileName].timeframeIndex,
                data: parsedGsData
            };
            data.push(d);
        }
        return data;
    }
}

export interface CVSXVolumeData {
    channelId: string
    timeframeIndex: number
    data: Uint8Array
}

export interface CVSXLatticeSegmentationData {
    segmentationId: string
    timeframeIndex: number
    data: Uint8Array
}

export interface QueryArgs {
    entry_id: string,
    source_db: Source,
    time?: number,
    channel_id?: string,
    segmentation_id?: string,
    detail_lvl?: number,
    max_points?: number
}