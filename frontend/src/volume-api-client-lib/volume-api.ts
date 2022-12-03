import { type Metadata } from './data';


function createApiPrefix() {
    const hostname = process.env.REACT_APP_API_HOSTNAME
        ? process.env.REACT_APP_API_HOSTNAME : `${window.location.protocol}//${window.location.hostname}`;
    const port = process.env.REACT_APP_API_PORT;
    const prefix = process.env.REACT_APP_API_PREFIX
        ? `/${process.env.REACT_APP_API_PREFIX}` : ``;

    return `${hostname}${port ? port : ''}${prefix}`;
}

function getGitTag() {
    return `${process.env.REACT_APP_GIT_TAG ?? ''}`;
}

function getGitSha() {
    return `${process.env.REACT_APP_GIT_SHA ?? ''}`;
}


// const DEFAULT_API_PREFIX = process.env.REACT_APP_VOLUME_API 
//     ? !process.env.REACT_APP_VOLUME_API.endsWith('/') ? `${process.env.REACT_APP_VOLUME_API}/` : process.env.REACT_APP_VOLUME_API 
//     : 'http://localhost:9000/';

const DEFAULT_API_PREFIX = createApiPrefix()
const GIT_TAG = getGitTag()
const GIT_SHA = getGitSha()

const DEFAULT_VOLUME_SERVER_V1 = `${DEFAULT_API_PREFIX}/v1`;
const DEFAULT_VOLUME_SERVER_V2 = `${DEFAULT_API_PREFIX}/v2`;

export class VolumeApiV1 {
    public volumeServerUrl: string;
    public volumeServerGitTag: string;
    public volumeServerGitSha: string;

    public constructor(
        volumeServerUrl: string = DEFAULT_VOLUME_SERVER_V1,
        volumeServerGitTag: string = GIT_TAG,
        volumeServerGitSha: string = GIT_SHA
        ) {
        this.volumeServerUrl = volumeServerUrl.replace(/\/$/, '');  // trim trailing slash
        this.volumeServerGitTag = volumeServerGitTag;
        this.volumeServerGitSha = volumeServerGitSha;
        console.log('API V1', this.volumeServerUrl)

        console.log(`SHA: ${this.volumeServerGitSha}`)
        console.log(`GIT TAG: ${this.volumeServerGitTag}`)
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
    public volumeServerGitTag: string;
    public volumeServerGitSha: string;
    
    public constructor(
        volumeServerUrl: string = DEFAULT_VOLUME_SERVER_V2,
        volumeServerGitTag: string = GIT_TAG,
        volumeServerGitSha: string = GIT_SHA
        ) {
        this.volumeServerUrl = volumeServerUrl.replace(/\/$/, '');  // trim trailing slash
        this.volumeServerGitTag = volumeServerGitTag;
        this.volumeServerGitSha = volumeServerGitSha;

        console.log('API V2', this.volumeServerUrl)
        console.log(`SHA: ${this.volumeServerGitSha}`)
        console.log(`GIT TAG: ${this.volumeServerGitTag}`)
    }

    public entryListUrl(maxEntries: number, keyword?: string): string {
        return `${this.volumeServerUrl}/list_entries/${maxEntries}/${keyword ?? ''}`;
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
        if (box) {
            const [[a1, a2, a3], [b1, b2, b3]] = box;
            return `${this.volumeServerUrl}/${source}/${entryId}/segmentation/box/${segmentation}/${a1}/${a2}/${a3}/${b1}/${b2}/${b3}?max_points=${maxPoints}`;
        } else {
            return `${this.volumeServerUrl}/${source}/${entryId}/segmentation/cell/${segmentation}?max_points=${maxPoints}`;
        }
    }
    public meshUrl_Json(source: string, entryId: string, segment: number, detailLevel: number): string {
        return `${this.volumeServerUrl}/${source}/${entryId}/mesh/${segment}/${detailLevel}`;
    }

    public meshUrl_Bcif(source: string, entryId: string, segment: number, detailLevel: number): string {
        return `${this.volumeServerUrl}/${source}/${entryId}/mesh_bcif/${segment}/${detailLevel}`;
    }
    public volumeInfoUrl(source: string, entryId: string): string {
        return `${this.volumeServerUrl}/${source}/${entryId}/volume_info`;
    }

    public async getEntryList(maxEntries: number, keyword?: string): Promise<{ [source: string]: string[] }> {
        const response = await fetch(this.entryListUrl(maxEntries, keyword));
        return await response.json();
    }

    public async getMetadata(source: string, entryId: string): Promise<Metadata> {
        const response = await fetch(this.metadataUrl(source, entryId));
        return await response.json();
    }
}
