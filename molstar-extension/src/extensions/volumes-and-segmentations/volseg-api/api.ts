/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Adam Midlik <midlik@gmail.com>
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */

import { DescriptionData, SegmentAnnotationData, type Meta, AnnotationsMetadata } from './data';


// export const DEFAULT_VOLSEG_SERVER = 'https://molstarvolseg.ncbr.muni.cz/v2';
export const DEFAULT_VOLSEG_SERVER = 'http://147.251.21.60:1111/v1';

export class VolumeApiV2 {
    public volumeServerUrl: string;

    public constructor(volumeServerUrl: string = DEFAULT_VOLSEG_SERVER) {
        this.volumeServerUrl = volumeServerUrl.replace(/\/$/, ''); // trim trailing slash
    }

    public async updateAnnotationsJson(source: string, entryId: string, annotationsJson: AnnotationsMetadata) {
        const url = `${this.volumeServerUrl}/${source}/${entryId}/annotations_json/update`;
        const obj = JSON.stringify({ annotations_json: annotationsJson });
        await fetch(url, {
            method: 'POST',
            body: obj,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    public async editDescriptionsUrl(source: string, entryId: string, descriptionData: DescriptionData[]) {
        const url = `${this.volumeServerUrl}/${source}/${entryId}/descriptions/edit`;
        const obj = JSON.stringify({ descriptions: descriptionData });
        await fetch(url, {
            method: 'POST',
            body: obj,
            headers: { 'Content-Type': 'application/json' }
        });
    }
    public async editSegmentAnnotationsUrl(source: string, entryId: string, segmentAnnotationData: SegmentAnnotationData[]) {
        const url = `${this.volumeServerUrl}/${source}/${entryId}/segment_annotations/edit`;
        const obj = JSON.stringify({ segment_annotations: segmentAnnotationData });
        await fetch(url, {
            method: 'POST',
            body: obj,
            headers: { 'Content-Type': 'application/json' }
        });
    }
    public async removeDescriptionsUrl(source: string, entryId: string, description_ids: string[]) {
        const url = `${this.volumeServerUrl}/${source}/${entryId}/descriptions/remove`;
        const obj = JSON.stringify({ description_ids: description_ids });
        await fetch(url, {
            method: 'POST',
            body: obj,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    public async removeSegmentAnnotationsUrl(source: string, entryId: string, annotation_ids: string[]) {
        const url = `${this.volumeServerUrl}/${source}/${entryId}/segment_annotations/remove`;
        const obj = JSON.stringify({ annotation_ids: annotation_ids });
        await fetch(url, {
            method: 'POST',
            body: obj,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    public entryListUrl(maxEntries: number, keyword?: string): string {
        return `${this.volumeServerUrl}/list_entries/${maxEntries}/${keyword ?? ''}`;
    }

    public metadataUrl(source: string, entryId: string): string {
        return `${this.volumeServerUrl}/${source}/${entryId}/metadata`;
    }
    public volumeUrl(source: string, entryId: string, timeframe: number, channelId: string, box: [[number, number, number], [number, number, number]] | null, maxPoints: number): string {
        if (box) {
            const [[a1, a2, a3], [b1, b2, b3]] = box;
            return `${this.volumeServerUrl}/${source}/${entryId}/volume/box/${timeframe}/${channelId}/${a1}/${a2}/${a3}/${b1}/${b2}/${b3}?max_points=${maxPoints}`;
        } else {
            return `${this.volumeServerUrl}/${source}/${entryId}/volume/cell/${timeframe}/${channelId}?max_points=${maxPoints}`;
        }
    }

    public latticeUrl(source: string, entryId: string, segmentation: string, timeframe: number, box: [[number, number, number], [number, number, number]] | null, maxPoints: number): string {
        if (box) {
            const [[a1, a2, a3], [b1, b2, b3]] = box;
            return `${this.volumeServerUrl}/${source}/${entryId}/segmentation/box/${segmentation}/${timeframe}/${a1}/${a2}/${a3}/${b1}/${b2}/${b3}?max_points=${maxPoints}`;
        } else {
            return `${this.volumeServerUrl}/${source}/${entryId}/segmentation/cell/${segmentation}/${timeframe}?max_points=${maxPoints}`;
        }
    }

    public geometricSegmentationUrl(source: string, entryId: string, segmentation_id: string, timeframe: number) {
        return `${this.volumeServerUrl}/${source}/${entryId}/geometric_segmentation/${segmentation_id}/${timeframe}`;
    }

    public meshUrl_Json(source: string, entryId: string, segmentation_id: string, timeframe: number, segment: number, detailLevel: number): string {
        return `${this.volumeServerUrl}/${source}/${entryId}/mesh/${segmentation_id}/${timeframe}/${segment}/${detailLevel}`;
    }

    public meshUrl_Bcif(source: string, entryId: string, segmentation_id: string, timeframe: number, segment: number, detailLevel: number): string {
        return `${this.volumeServerUrl}/${source}/${entryId}/mesh_bcif/${segmentation_id}/${timeframe}/${segment}/${detailLevel}`;
    }

    public volumeInfoUrl(source: string, entryId: string): string {
        return `${this.volumeServerUrl}/${source}/${entryId}/volume_info`;
    }

    public async getEntryList(maxEntries: number, keyword?: string): Promise<{ [source: string]: string[] }> {
        const response = await fetch(this.entryListUrl(maxEntries, keyword));
        return await response.json();
    }

    public async getMetadata(source: string, entryId: string): Promise<Meta> {
        const url = this.metadataUrl(source, entryId);
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Failed to fetch metadata from ${url}`);
        return await response.json();
    }
}
