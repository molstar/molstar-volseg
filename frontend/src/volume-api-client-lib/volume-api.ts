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
    public volumeAndLatticeUrl(source: string, entryId: string, segmentation: number, box: [[number, number, number], [number, number, number]], maxPoints: number): string {
        const [[a1, a2, a3], [b1, b2, b3]] = box;
        return `${this.volumeServerUrl}/${source}/${entryId}/box/${segmentation}/${a1}/${a2}/${a3}/${b1}/${b2}/${b3}/${maxPoints}`;
    }
    public meshUrl(source: string, entryId: string, segment: number, detailLevel: number): string {
        return `${this.volumeServerUrl}/${source}/${entryId}/mesh/${segment}/${detailLevel}`;
    }

    public async getMetadata(source: string, entryId: string): Promise<Metadata> {
        const response = await fetch(this.metadataUrl(source, entryId));
        return await response.json();
    }
}

export class VolumeApiV2 {
    public volumeServerUrl: string;

    public constructor(volumeServerUrl: string = DEFAULT_VOLUME_SERVER_V2) {
        this.volumeServerUrl = volumeServerUrl.replace(/\/$/, '');  // trim trailing slash
    }
    
    public metadataUrl(source: string, entryId: string): string {
        return `${this.volumeServerUrl}/${source}/${entryId}/metadata`;
    }
    public volumeUrl(source: string, entryId: string, box: [[number, number, number], [number, number, number]] | null, maxPoints: number): string {
        if (box) {
            const [[a1, a2, a3], [b1, b2, b3]] = box;
            return `${this.volumeServerUrl}/${source}/${entryId}/volume/box/${a1}/${a2}/${a3}/${b1}/${b2}/${b3}?max_points=${maxPoints}`;
        } else {
            return `${this.volumeServerUrl}/${source}/${entryId}/volume/cell?max_points=${maxPoints}`;
        }
    }
    public latticeUrl(source: string, entryId: string, segmentation: number, box: [[number, number, number], [number, number, number]] | null, maxPoints: number): string {
        if (box){
            const [[a1, a2, a3], [b1, b2, b3]] = box;
            return `${this.volumeServerUrl}/${source}/${entryId}/segmentation/box/${segmentation}/${a1}/${a2}/${a3}/${b1}/${b2}/${b3}?max_points=${maxPoints}`;
        } else {
            return `${this.volumeServerUrl}/${source}/${entryId}/segmentation/cell/${segmentation}?max_points=${maxPoints}`;
        }
    }
    public meshUrl(source: string, entryId: string, segment: number, detailLevel: number): string {
        return `${this.volumeServerUrl}/${source}/${entryId}/mesh/${segment}/${detailLevel}`;
    }

    public meshUrl_Bcif(source: string, entryId: string, segment: number, detailLevel: number): string {
        return `${this.volumeServerUrl}/${source}/${entryId}/mesh_bcif/${segment}/${detailLevel}`;
    }
    public volumeInfoUrl(source: string, entryId: string): string {
        return `${this.volumeServerUrl}/${source}/${entryId}/volume_info`;
    }

    public async getMetadata(source: string, entryId: string): Promise<Metadata> {
        const response = await fetch(this.metadataUrl(source, entryId));
        return await response.json();
    }
}
