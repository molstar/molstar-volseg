import { type Metadata, Annotation, Segment } from './data';


const DEFAULT_VOLUME_SERVER_V1 = 'http://localhost:9000/v1';
const DEFAULT_VOLUME_SERVER_V2 = 'http://localhost:9000/v2';


export class VolumeApiV1 {
    public volumeServerUrl: string;

    public constructor(volumeServerUrl: string = DEFAULT_VOLUME_SERVER_V1) {
        this.volumeServerUrl = volumeServerUrl.replace(/\/$/, '');  // trim trailing slash
    }
    
    public metadataUrl(source: string, entryId: string): string {
        return `${this.volumeServerUrl}/${source}/${entryId}/metadata`;
    }
    public volumeServerRequestUrl(source: string, entryId: string, segmentation: number, box: [[number, number, number], [number, number, number]], maxPoints: number): string {
        const [[a1, a2, a3], [b1, b2, b3]] = box;
        return `${this.volumeServerUrl}/${source}/${entryId}/box/${segmentation}/${a1}/${a2}/${a3}/${b1}/${b2}/${b3}/${maxPoints}`;
    }
    public meshServerRequestUrl(source: string, entryId: string, segment: number, detailLevel: number): string {
        return `${this.volumeServerUrl}/${source}/${entryId}/mesh/${segment}/${detailLevel}`;
    }

    public async getMetadata(source: string, entryId: string): Promise<Metadata> {
        const response = await fetch(this.metadataUrl(source, entryId));
        return await response.json();
    }
}