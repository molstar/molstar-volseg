import { PluginUIContext } from 'molstar/lib/mol-plugin-ui/context';
import { StateTransformer } from 'molstar/lib/mol-state';
import { PluginStateObject } from 'molstar/lib/mol-plugin-state/objects';
import { Grid, Volume } from 'molstar/lib/mol-model/volume';
import { ParamDefinition as PD } from 'molstar/lib/mol-util/param-definition';
import { CustomProperties } from 'molstar/lib/mol-model/custom-property';
import { CIF, CifBlock } from 'molstar/lib/mol-io/reader/cif';
import { volumeFromDensityServerData } from 'molstar/lib/mol-model-formats/volume/density-server'

import { type Metadata, Segment } from './volume-api-client-lib/data';


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


export type ExampleType = '' | 'xEmdb' | 'xBioimage' | 'xMeshes' | 'xMeshStreaming' | 'xAuto';



export class LatticeSegmentation {
    private segmentationValues: ReadonlyArray<number>;
    private segmentMap;
    private grid: Grid;

    private constructor(segmentationDataBlock: CifBlock, grid: Grid) {
        this.segmentationValues = segmentationDataBlock!.categories['segmentation_data_3d'].getField('values')?.toIntArray()!;
        this.segmentMap = LatticeSegmentation.makeSegmentMap(segmentationDataBlock);
        this.grid = grid;
    }

    public static async fromCifBlock(plugin: PluginUIContext, segmentationDataBlock: CifBlock){
        const densityServerCif = CIF.schema.densityServer(segmentationDataBlock);
        // console.log('dscif', densityServerCif);
        const volume = await plugin.runTask(volumeFromDensityServerData(densityServerCif));
        // console.log('volume', volume);
        const grid = volume.grid;
        return new LatticeSegmentation(segmentationDataBlock, grid);
    }

    public createSegment(segId: number): Volume {
        const n = this.segmentationValues.length;
        const newData = new Float32Array(n);

        for (let i = 0; i < n; i++) {
            newData[i] = this.segmentMap.get(this.segmentationValues[i])?.has(segId) ? 1 : 0;
        }

        return {
            sourceData: { kind: 'custom', name: 'test', data: newData as any },
            customProperties: new CustomProperties(),
            _propertyData: {},
            grid: {
                ...this.grid,
                //stats: { min: 0, max: 1, mean: newMean, sigma: arrayRms(newData) },
                stats: { min: 0, max: 1, mean: 0, sigma: 1 },
                cells: {
                    ...this.grid.cells,
                    data: newData as any,
                }
            }
        };
    }

    private static makeSegmentMap(segmentationDataBlock: CifBlock): Map<number, Set<number>> {
        const setId = segmentationDataBlock.categories['segmentation_data_table'].getField('set_id')?.toIntArray()!;
        const segmentId = segmentationDataBlock.categories['segmentation_data_table'].getField('segment_id')?.toIntArray()!;
        const map = new Map<number, Set<number>>();
        for (let i = 0; i < segmentId.length; i++) {
            if (!map.has(setId[i])) {
                map.set(setId[i], new Set());
            }
            map.get(setId[i])!.add(segmentId[i]);
        }
        return map;
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
        volume: PD.Value<Volume>(undefined as any, { isHidden: true }),
    }
})({
    apply({ params }) {
        return new PluginStateObject.Volume.Data(params.volume);
    }
})