import { CifFile } from 'molstar/lib/mol-io/reader/cif';
import { Volume } from 'molstar/lib/mol-model/volume';
import { PluginStateObject } from 'molstar/lib/mol-plugin-state/objects';
import { StateTransforms } from 'molstar/lib/mol-plugin-state/transforms';
import { CreateGroup } from 'molstar/lib/mol-plugin-state/transforms/misc';
import { PluginUIContext } from 'molstar/lib/mol-plugin-ui/context';
import { setSubtreeVisibility } from 'molstar/lib/mol-plugin/behavior/static/state';
import { StateBuilder, StateObjectSelector, StateTransform, StateTransformer } from 'molstar/lib/mol-state';
import { ParamDefinition as PD } from 'molstar/lib/mol-util/param-definition';

import { Segment, type Metadata } from '../volume-api-client-lib/data';
import { VolumeApiV2 } from '../volume-api-client-lib/volume-api';


export type ExampleType = 'emdb' | 'bioimage' | 'meshes' | 'meshStreaming' | 'auto';


export namespace MetadataUtils {
    export function meshSegments(metadata: Metadata): number[] {
        const segmentIds = metadata.grid.segmentation_meshes.mesh_component_numbers.segment_ids;
        if (segmentIds === undefined) return [];
        return Object.keys(segmentIds).map(s => parseInt(s));
    }
    export function meshSegmentDetails(metadata: Metadata, segmentId: number): number[] {
        const segmentIds = metadata.grid.segmentation_meshes.mesh_component_numbers.segment_ids;
        if (segmentIds === undefined) return [];
        const details = segmentIds[segmentId].detail_lvls;
        return Object.keys(details).map(s => parseInt(s));
    }
    /** Get the worst available detail level that is not worse than preferredDetail. 
     * If preferredDetail is null, get the worst detail level overall.
     * (worse = greater number) */
    export function getSufficientDetail(metadata: Metadata, segmentId: number, preferredDetail: number | null) {
        let availDetails = meshSegmentDetails(metadata, segmentId);
        if (preferredDetail !== null) {
            availDetails = availDetails.filter(det => det <= preferredDetail);
        }
        return Math.max(...availDetails);
    }
    export function annotationsBySegment(metadata: Metadata): { [id: number]: Segment } {
        const result: { [id: number]: Segment } = {};
        for (const segment of metadata.annotation.segment_list) {
            if (segment.id in result) {
                throw new Error(`Duplicate segment annotation for segment ${segment.id}`);
            }
            result[segment.id] = segment;
        }
        return result;
    }
    export function dropSegments(metadata: Metadata, segments: number[]): void {
        if (metadata.grid.segmentation_meshes.mesh_component_numbers.segment_ids === undefined) return;
        const dropSet = new Set(segments);
        metadata.annotation.segment_list = metadata.annotation.segment_list.filter(seg => !dropSet.has(seg.id));
        for (const seg of segments) {
            delete metadata.grid.segmentation_meshes.mesh_component_numbers.segment_ids[seg];
        }
    }
}


export interface UrlFragmentInfo {
    example?: ExampleType,
    entry?: string,
}
export namespace UrlFragmentInfo {
    export function get(): UrlFragmentInfo {
        const fragment = window.location.hash.replace('#', '');
        return Object.fromEntries(new URLSearchParams(fragment).entries())
    }
    export function set(urlFragmentInfo: UrlFragmentInfo): void {
        const fragment = new URLSearchParams(urlFragmentInfo).toString();
        window.location.hash = fragment;
    }
}


const CreateTransformer = StateTransformer.builderFactory('cellstar');

export const CreateVolume = CreateTransformer({
    name: 'create-transformer',
    from: PluginStateObject.Root,
    to: PluginStateObject.Volume.Data,
    params: {
        label: PD.Text('Volume', { isHidden: true }),
        description: PD.Text('', { isHidden: true }),
        volume: PD.Value<Volume>(undefined as any, { isHidden: true }),
    }
})({
    apply({ params }) {
        return new PluginStateObject.Volume.Data(params.volume, { label: params.label, description: params.description });
    }
})


export class NodeManager {
    private nodes: { [key: string]: StateObjectSelector };

    constructor() {
        this.nodes = {};
    }

    private static nodeExists(node: StateObjectSelector): boolean {
        try {
            return node.checkValid();
        } catch {
            return false;
        }
    }

    public getNode(key: string): StateObjectSelector | undefined {
        const node = this.nodes[key];
        if (node && !NodeManager.nodeExists(node)) {
            delete this.nodes[key];
            return undefined;
        }
        return node;
    }

    public getNodes(): StateObjectSelector[] {
        return Object.keys(this.nodes).map(key => this.getNode(key)).filter(node => node) as StateObjectSelector[];
    }

    public deleteAllNodes(update: StateBuilder.Root) {
        for (const node of this.getNodes()) {
            update.delete(node);
        }
        this.nodes = {};
    }

    public hideAllNodes() {
        for (const node of this.getNodes()) {
            setSubtreeVisibility(node.state!, node.ref, true);  // hide
        }
    }

    public async showNode(key: string, factory: () => StateObjectSelector | Promise<StateObjectSelector>) {
        let node = this.getNode(key);
        if (node) {
            setSubtreeVisibility(node.state!, node.ref, false);  // show
        } else {
            node = await factory();
            this.nodes[key] = node;
        }
        return node;
    }

}


/** Split entry ID (e.g. 'emd-1832') into source ('emdb') and number ('1832') */
export function splitEntryId(entryId: string) {
    const PREFIX_TO_SOURCE: { [prefix: string]: string } = { 'empiar': 'empiar', 'emd': 'emdb' };
    const [prefix, entry] = entryId.split('-');
    return {
        source: PREFIX_TO_SOURCE[prefix],
        entryNumber: entry
    };
}

/** Create entry ID (e.g. 'emd-1832') for a combination of source ('emdb') and number ('1832') */
export function createEntryId(source: string, entryNumber: string | number) {
    const SOURCE_TO_PREFIX: { [prefix: string]: string } = { 'empiar': 'empiar', 'emdb': 'emd' };
    return `${SOURCE_TO_PREFIX[source]}-${entryNumber}`;
}


export namespace Debugging {
    export function logCifOverview(cifData: CifFile, url: string = ''): void {
        const MAX_VALUES = 10;
        console.log('CifFile', url);
        cifData.blocks.forEach(block => {
            console.log(`    ${block.header}`);
            block.categoryNames.forEach(catName => {
                const category = block.categories[catName];
                const nRows = category.rowCount;
                console.log(`        _${catName} [${nRows} rows]`);
                category.fieldNames.forEach(fieldName => {
                    const field = category.getField(fieldName);
                    let values = field?.toStringArray().slice(0, MAX_VALUES).join(', ');
                    if (nRows > MAX_VALUES) values += '...';
                    console.log(`            .${fieldName}:  ${values}`);
                });
            });
        });
    }

    export async function testApiV2(plugin: PluginUIContext, api: VolumeApiV2) {
        const A = 10 ** 5;
        const BOX: [[number, number, number], [number, number, number]] = [[-A, -A, -A], [A, A, A]];
        const MAX_VOXELS = 10 ** 7;
        const urls: { [name: string]: string } = {
            'VOLUME BOX EMD-1832': api.volumeUrl('emdb', 'emd-1832', BOX, MAX_VOXELS),
            'LATTICE BOX EMD-1832': api.latticeUrl('emdb', 'emd-1832', 0, BOX, MAX_VOXELS),
            'VOLUME CELL EMD-1832': api.volumeUrl('emdb', 'emd-1832', null, MAX_VOXELS),
            'LATTICE CELL EMD-1832': api.latticeUrl('emdb', 'emd-1832', 0, null, MAX_VOXELS),
            'VOLUME BOX EMPIAR-10070': api.volumeUrl('empiar', 'empiar-10070', BOX, MAX_VOXELS),
            'VOLUME CELL EMPIAR-10070': api.volumeUrl('empiar', 'empiar-10070', null, MAX_VOXELS),
            // 'VOLUME CELL EMD-1832': api.volumeUrl('emdb', 'emd-1832', null, MAX_VOXELS),
            // 'VOLUME CELL EMD-1832 EBI': 'https://www.ebi.ac.uk/pdbe/densities/emd/emd-1832/cell?detail=5',
            // 'VOLUME CELL EMD-1547': api.volumeUrl('emdb', 'emd-1547', null, MAX_VOXELS),
            // 'VOLUME CELL EMD-1547 EBI': 'https://www.ebi.ac.uk/pdbe/densities/emd/emd-1547/cell?detail=5',
            // 'VOLUME CELL EMD-1181': api.volumeUrl('emdb', 'emd-1181', null, MAX_VOXELS),
            // 'VOLUME CELL EMD-1181 EBI': 'https://www.ebi.ac.uk/pdbe/densities/emd/emd-1181/cell?detail=5',
        };
        for (const name in urls) {
            console.log(`\n<<< ${name} >>>`);
            console.log(urls[name]);
            try {
                const data = await plugin.builders.data.download({ url: urls[name], isBinary: true });
                const cif = await plugin.build().to(data).apply(StateTransforms.Data.ParseCif).commit();
                logCifOverview(cif.data!, urls[name]);
                await testVolumeBbox(plugin, urls[name], 1.0);
            } catch (err) {
                console.error('Failed', err);
            }
        }
    }

    export async function testVolumeBbox(plugin: PluginUIContext, url: string, isoValue: number) {
        const volumeDataNode = await plugin.builders.data.download({ url: url, isBinary: true });
        const parsed = await plugin.dataFormats.get('dscif')!.parse(plugin, volumeDataNode, { entryId: url });
        const volume: StateObjectSelector<PluginStateObject.Volume.Data> = parsed.volumes?.[0] ?? parsed.volume;
        const volumeData = volume.cell!.obj!.data;
        const space = volumeData.grid.cells.space;
        const data = volumeData.grid.cells.data;
        console.log('testVolumeBbox', url, 'axisOrderSlowToFast:', space.axisOrderSlowToFast, 'dimensions:', space.dimensions);
        const [nx, ny, nz] = space.dimensions;

        let minX = nx, minY = ny, minZ = nz;
        let maxX = -1, maxY = -1, maxZ = -1;
        for (let iz = 0; iz < nz; iz++) {
            for (let iy = 0; iy < ny; iy++) {
                for (let ix = 0; ix < nx; ix++) {
                    // Iterating in ZYX order is faster (probably fewer cache misses)
                    if (space.get(data, ix, iy, iz) >= isoValue) {
                        if (ix < minX) minX = ix;
                        if (iy < minY) minY = iy;
                        if (iz < minZ) minZ = iz;
                        if (ix > maxX) maxX = ix;
                        if (iy > maxY) maxY = iy;
                        if (iz > maxZ) maxZ = iz;
                    }
                }
            }
        }
        console.log(`bbox (value>=${isoValue}):`, [minX, minY, minZ], [maxX + 1, maxY + 1, maxZ + 1], 'size:', [maxX - minX + 1, maxY - minY + 1, maxZ - minZ + 1]);
    }
}