import { createPluginUI } from 'molstar/lib/mol-plugin-ui/react18';
import { PluginUIContext } from 'molstar/lib/mol-plugin-ui/context';
import { DefaultPluginUISpec } from 'molstar/lib/mol-plugin-ui/spec';
import { PluginConfig } from 'molstar/lib/mol-plugin/config';
import { StateBuilder, StateObjectSelector, StateTransform, StateTransformer } from 'molstar/lib/mol-state';
import { PluginStateObject } from 'molstar/lib/mol-plugin-state/objects';
import { StateTransforms } from 'molstar/lib/mol-plugin-state/transforms';
import { createVolumeRepresentationParams } from 'molstar/lib/mol-plugin-state/helpers/volume-representation-params';
import { Volume } from 'molstar/lib/mol-model/volume';
import { Color } from 'molstar/lib/mol-util/color';
import { ParamDefinition as PD } from 'molstar/lib/mol-util/param-definition';
import { CustomProperties } from 'molstar/lib/mol-model/custom-property';
import { arrayMean, arrayRms } from 'molstar/lib/mol-util/array';
import { Vec2 } from 'molstar/lib/mol-math/linear-algebra';
import { BehaviorSubject } from 'rxjs';
import { setSubtreeVisibility } from 'molstar/lib/mol-plugin/behavior/static/state';

import * as MeshExamples from './mesh-extension/examples'
import { ColorNames } from './mesh-extension/molstar-lib-imports';
import { type Metadata, Annotation, Segment } from './volume-api-client-lib/data';

const VOLUME_SERVER = 'http://localhost:9000';
const DEFAULT_DETAIL: number|null = null;  // null means worst


namespace Metadata {
    export function meshSegments(metadata: Metadata): number[] {
        const segmentIds = metadata.grid.segmentation_meshes.mesh_component_numbers.segment_ids;
        return Object.keys(segmentIds).map(s => parseInt(s));
    }
    export function meshSegmentDetails(metadata: Metadata, segmentId: number): number[] {
        const details = metadata.grid.segmentation_meshes.mesh_component_numbers.segment_ids[segmentId].detail_lvls;
        return Object.keys(details).map(s => parseInt(s));
    }
    /** Get the worst available detail level that is not worse than preferredDetail. 
     * If preferredDetail is null, get the worst detail level overall.
     * (worse = greater number) */
    export function getSufficientDetail(metadata: Metadata, segmentId: number, preferredDetail: number|null){
        let availDetails = meshSegmentDetails(metadata, segmentId);
        if (preferredDetail !== null){
            availDetails = availDetails.filter(det => det <= preferredDetail);
        }
        return Math.max(...availDetails);
    }
    export function annotationsBySegment(metadata: Metadata): {[id: number]: Segment}{
        const result: {[id: number]: Segment} = {};
        for (const segment of metadata.annotation.segment_list){
            if (segment.id in result) {
                throw new Error(`Duplicate segment annotation for segment ${segment.id}`);
            }
            result[segment.id] = segment;
        }
        return result;
    }
    export function dropSegments(metadata: Metadata, segments: number[]): void {
        const dropSet = new Set(segments);
        metadata.annotation.segment_list = metadata.annotation.segment_list.filter(seg => !dropSet.has(seg.id));
        for (const seg of segments) {
            delete metadata.grid.segmentation_meshes.mesh_component_numbers.segment_ids[seg];
        }
    }
}

export class AppModel {
    plugin: PluginUIContext = void 0 as any;

    async init(target: HTMLElement) {
        const defaultSpec = DefaultPluginUISpec();
        this.plugin = await createPluginUI(target, {
            ...defaultSpec,
            layout: {
                initial: {
                    isExpanded: false,
                    showControls: true,  // original: false
                    controlsDisplay: 'landscape',  // original: not given
                },
            },
            components: {
                // controls: { left: 'none', right: 'none', top: 'none', bottom: 'none' },
                controls: { right: 'none', top: 'none', bottom: 'none' },
            },
            canvas3d: {
                camera: {
                    helper: { axes: { name: 'off', params: {} } }
                }
            },
            config: [
                [PluginConfig.Viewport.ShowExpand, true],  // original: false
                [PluginConfig.Viewport.ShowControls, true],  // original: false
                [PluginConfig.Viewport.ShowSelectionMode, false],
                [PluginConfig.Viewport.ShowAnimation, false],
            ],
        });

        // setTimeout(() => this.load1832(), 50);
        setTimeout(() => this.load10070(), 50);
    }

    createFakeSegment(volume: Volume, level: number): Volume {
        const { mean, sigma } = volume.grid.stats;
        const { data, space } = volume.grid.cells;
        const newData = new Float32Array(data.length);

        for (let i = 0; i < space.dimensions[0]; i++) {
            if (Math.floor(10 * i / space.dimensions[0]) !== level) continue;

            for (let j = 0; j < space.dimensions[1]; j++) {
                for (let k = 0; k < space.dimensions[2]; k++) {
                    const o = space.dataOffset(i, j, k);
                    const v = (data[o] - mean) / sigma;
                    if (v > 2.5) newData[o] = 1;
                }
            }   
        }

        return {
            sourceData: { kind: 'custom', name: 'test', data: newData as any },
            customProperties: new CustomProperties(),
            _propertyData: {},
            grid: {
                ...volume.grid,
                //stats: { min: 0, max: 1, mean: newMean, sigma: arrayRms(newData) },
                stats: { min: 0, max: 1, mean: 0, sigma: 1 },
                cells: {
                    ...volume.grid.cells,
                    data: newData as any,
                }
            }
        };
    }

    createSegment99999Plus(volume: Volume, threshold: number): Volume {
        const { mean, sigma } = volume.grid.stats;
        const { data, space } = volume.grid.cells;
        const newData = new Float32Array(data.length);

        for (let i = 0; i < space.dimensions[0]; i++) {
            for (let j = 0; j < space.dimensions[1]; j++) {
                for (let k = 0; k < space.dimensions[2]; k++) {
                    const o = space.dataOffset(i, j, k);
                    const v = (data[o] - mean) / sigma;
                    if (v > threshold) newData[o] = 1;
                }
            }   
        }

        return {
            sourceData: { kind: 'custom', name: 'test', data: newData as any },
            customProperties: new CustomProperties(),
            _propertyData: {},
            grid: {
                ...volume.grid,
                //stats: { min: 0, max: 1, mean: newMean, sigma: arrayRms(newData) },
                stats: { min: 0, max: 1, mean: 0, sigma: 1 },
                cells: {
                    ...volume.grid.cells,
                    data: newData as any,
                }
            }
        };
    }

    createSegment99999Minus(volume: Volume, threshold: number): Volume {
        const { mean, sigma } = volume.grid.stats;
        const { data, space } = volume.grid.cells;
        const newData = new Float32Array(data.length);

        for (let i = 0; i < space.dimensions[0]; i++) {
            for (let j = 0; j < space.dimensions[1]; j++) {
                for (let k = 0; k < space.dimensions[2]; k++) {
                    const o = space.dataOffset(i, j, k);
                    const v = (data[o] - mean) / sigma;
                    if (v > threshold && v < -0.35) newData[o] = 1;
                }
            }   
        }

        return {
            sourceData: { kind: 'custom', name: 'test', data: newData as any },
            customProperties: new CustomProperties(),
            _propertyData: {},
            grid: {
                ...volume.grid,
                //stats: { min: 0, max: 1, mean: newMean, sigma: arrayRms(newData) },
                stats: { min: 0, max: 1, mean: 0, sigma: 1 },
                cells: {
                    ...volume.grid.cells,
                    data: newData as any,
                }
            }
        };
    }

    createSegment(volume: Volume, segmentation: number[], segId: number): Volume {
        const { mean, sigma } = volume.grid.stats;
        const { data, space } = volume.grid.cells;
        const newData = new Float32Array(data.length);

        for (let i = 0; i < data.length; i++) {
            newData[i] = segmentation[i] === segId ? 1 : 0;
        }

        return {
            sourceData: { kind: 'custom', name: 'test', data: newData as any },
            customProperties: new CustomProperties(),
            _propertyData: {},
            grid: {
                ...volume.grid,
                //stats: { min: 0, max: 1, mean: newMean, sigma: arrayRms(newData) },
                stats: { min: 0, max: 1, mean: 0, sigma: 1 },
                cells: {
                    ...volume.grid.cells,
                    data: newData as any,
                }
            }
        };
    }

    private volume: Volume = undefined as any;
    private currentLevel: any[] = [];

    async showSegments(segments: Segment[]) {        
        if (segments.length === 1) {
            this.currentSegment.next(segments[0]);
        } else {
            this.currentSegment.next(undefined);
        }

        const update = this.plugin.build();

        for (const l of this.currentLevel) update.delete(l);
        this.currentLevel = [];

        for (const s of segments) {
            const volume = this.createSegment(this.volume, this.segmentation, s.id);
            const root = update.toRoot().apply(CreateVolume, { volume });
            this.currentLevel.push(root.selector);

            root.apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volume, {
                type: 'isosurface',
                typeParams: { alpha: 1, isoValue: Volume.IsoValue.absolute(0.95) },
                color: 'uniform',
                colorParams: { value: Color.fromNormalizedArray(s.colour, 0) }
            }));
        }

        // const controlPoints: Vec2[] = [
        //     Vec2.create(0, 0),
        //     Vec2.create(0.5, 0),
        //     Vec2.create(0.98, 1),
        //     Vec2.create(1.1, 1),
        // ]

        // // const list = {
        // //     kind: 'interpolate' as const,
        // //     colors: [
        // //         [Color(0x0), 0]
        // //     ]
        // // }

        // root.apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volume, {
        //     type: 'direct-volume',
        //     typeParams: { 
        //         ignoreLight: true,
        //         stepsPerCell: 1,
        //         controlPoints,
        //         xrayShaded: false,
        //     },
        //     color: 'uniform',
        //     colorParams: { value: Color(Math.round(Math.random() * 0xffffff)) }
        // }));

        await update.commit();
    }

    private currentSegments: any[] = [];

    async showSegment(volume: Volume, color: number[], opacity = 1) {     
        const update = this.plugin.build();
        const root = update.toRoot().apply(CreateVolume, { volume });
        this.currentLevel.push(root.selector);

        const seg = root.apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volume, {
            type: 'isosurface',
            typeParams: { alpha: opacity, isoValue: Volume.IsoValue.absolute(0.95), transparentBackfaces: 'off', doubleSided: false, flatShaded: true },
            color: 'uniform',
            colorParams: { value: Color.fromNormalizedArray(color, 0) }
        }));

        this.currentSegments.push(seg.selector);

        await update.commit();
    }

    private segmentation: number[] = [];
    entryId = new BehaviorSubject<string>('');
    annotation = new BehaviorSubject<Annotation | undefined>(undefined);
    currentSegment = new BehaviorSubject<Segment | undefined>(undefined);
    error = new BehaviorSubject<any>(undefined);


    metadataUrl(source: string, entryId: string): string {
        return `http://localhost:9000/v1/${source}/${entryId}/metadata`;
    }
    volumeServerRequestUrl(source: string, entryId: string, segmentation: number, box: [[number, number, number], [number, number, number]], maxPoints: number): string {
        const [[a1, a2, a3], [b1, b2, b3]] = box;
        return `${VOLUME_SERVER}/v1/${source}/${entryId}/box/${segmentation}/${a1}/${a2}/${a3}/${b1}/${b2}/${b3}/${maxPoints}`;
    }
    // Temporary solution
    meshServerRequestUrl(source: string, entryId: string, segment: number, detailLevel: number): string{
        return `${VOLUME_SERVER}/v1/${source}/${entryId}/mesh/${segment}/${detailLevel}`;
    }

    async getMetadata(source: string, entryId: string): Promise<Metadata> {
        const response = await fetch(this.metadataUrl(source, entryId));
        return await response.json();
    }
    async getMeshData_debugging(source: string, entryId: string, segment: number, detailLevel: number){
        const url = this.meshServerRequestUrl(source, entryId, segment, detailLevel);
        const response = await fetch(url);
        const data = await response.json();
        return data;
    }

    logStuff(plugin: PluginUIContext, repr: StateBuilder.Root): void{
        console.log('plugin:\n', plugin);
        console.log('repr:\n', repr);
        console.log('tree:\n', repr.currentTree);
        console.log('children:', repr.currentTree.children.size);
    }
    
    private metadata?: Metadata = undefined;
    private meshSegmentNodes: {[segid: number]: any} = {};

    async showMeshSegments(segments: Segment[], entryId: string){  
        if (segments.length === 1) {
            this.currentSegment.next(segments[0]);
        } else {
            this.currentSegment.next(undefined);
        }

        for (const node of Object.values(this.meshSegmentNodes)) {
            setSubtreeVisibility(node.state!, node.ref, true);  // hide
        }
        for (const seg of segments) {
            let node = this.meshSegmentNodes[seg.id];
            if (!node) {
                const detail = Metadata.getSufficientDetail(this.metadata!, seg.id, DEFAULT_DETAIL);
                const color = seg.colour.length >= 3 ? Color.fromNormalizedArray(seg.colour, 0) : ColorNames.gray;
                node = await MeshExamples.createMeshFromUrl(this.plugin, this.meshServerRequestUrl(this.splitEntryId(entryId).source, entryId, seg.id, detail), seg.id, detail, true, false, color);
                this.meshSegmentNodes[seg.id] = node;
            }
            setSubtreeVisibility(node.state!, node.ref, false);  // show
        }
    }

    async load10070(entryId: string = 'empiar-10070') {
        const source = this.splitEntryId(entryId).source;
        const segments = 'fg';
        let error = undefined;

        try {
            await this.plugin.clear();
            // Testing API:
            // try {
            //     const meshes = await this.getMeshData_debugging('empiar', 'empiar-10070', 1, 7);
            //     console.log('Meshes from API:\n', meshes);
            // } catch {
            //     console.error('Could not get mesh data from API (maybe API not running?)');
            // }
            // await this.plugin.clear();

            // Examples for mesh visualization - currently taking static data stored on a MetaCentrum VM
            // MeshExamples.runMeshExample(this.plugin, 'fg', 'http://sestra.ncbr.muni.cz/data/cellstar-sample-data/db');
            // MeshExamples.runMultimeshExample(this.plugin, 'fg', 'worst', 'http://sestra.ncbr.muni.cz/data/cellstar-sample-data/db');  // Multiple segments merged into 1 segment with multiple meshes
            
            this.metadata = await this.getMetadata(source, entryId);
            if (segments === 'fg'){
                const bgSegments = [13, 15];
                Metadata.dropSegments(this.metadata, bgSegments);
            }
            
            for (let segment of this.metadata!.annotation.segment_list) {
                const detail = Metadata.getSufficientDetail(this.metadata!, segment.id, DEFAULT_DETAIL);
                // console.log(`Annotation: segment ${segment.id}. ${segment.biological_annotation.name} ${segment.colour} ${detail}`);
                // QUESTION: hmm, shouldn't it be "color"?
            }
            
            this.meshSegmentNodes = {};
            this.showMeshSegments(this.metadata!.annotation.segment_list, entryId);
        } catch (ex) {
            this.metadata = undefined;
            error = ex;
            throw ex;
        } finally {
            this.entryId.next(entryId);
            this.annotation.next(this.metadata?.annotation);
            this.dataSource.next('10070');  // This is not actual entry number just selector of example (10070 = mesh example)
            this.error.next(error);
        }
    }

    async load1832() {
        const entryId = 'emd-1832';
        const isoLevel = 2.73;
        // const url = `https://maps.rcsb.org/em/${entryId}/cell?detail=6`;
        const url = this.volumeServerRequestUrl('emdb', entryId, 0, [[-1000, -1000, -1000], [1000, 1000, 1000]], 100000000);
        const { plugin } = this;

        await plugin.clear();

        const data = await plugin.builders.data.download({ url, isBinary: true }, { state: { isGhost: true } });
        const parsed = await plugin.dataFormats.get('dscif')!.parse(plugin, data, { entryId });
        const volume: StateObjectSelector<PluginStateObject.Volume.Data> = parsed.volumes?.[0] ?? parsed.volume;
        const volumeData = volume.cell!.obj!.data;
        this.volume = volumeData;

        const cif = await plugin.build().to(data).apply(StateTransforms.Data.ParseCif).commit();
        const segmentation = cif.data!.blocks[2];

        const values = segmentation.categories['segmentation_data_3d'].getField('values')?.toIntArray();

        const metadata: Metadata = await (await fetch(`http://localhost:9000/v1/emdb/${entryId}/metadata`)).json();

        console.log('annotation:', metadata.annotation);

        this.entryId.next(entryId);
        this.annotation.next(metadata.annotation);
        this.segmentation = values as any;

        const repr = plugin.build();

        repr
            .to(volume)
            .apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volumeData, {
                type: 'isosurface',
                typeParams: { alpha: 0.2, isoValue: Volume.adjustedIsoValue(volumeData, isoLevel, 'relative') },
                color: 'uniform',
                colorParams: { value: Color(0x121212) }
            }));

        await repr.commit();

        await this.showSegments(metadata.annotation.segment_list);

        this.dataSource.next('1832');
    }

    dataSource = new BehaviorSubject<string>('');

    async setIsoValue(newValue: number, showSegmentation: boolean) {
        if (!this.repr) return;

        const { plugin } = this;
        await plugin.build().to(this.repr).update(createVolumeRepresentationParams(this.plugin, this.volume, {
            type: 'isosurface',
            typeParams: { alpha: showSegmentation ? 0.0 : 1, isoValue: Volume.IsoValue.relative(newValue) },
            color: 'uniform',
            colorParams: { value: showSegmentation ? Color(0x777777) : Color(0x224899) }
        })).commit();

        const update = this.plugin.build();

        for (const l of this.currentSegments) update.delete(l);
        this.currentSegments = [];
        await update.commit();

        if (showSegmentation) {
            const segP = this.createSegment99999Plus(this.volume, -0.35);
            const segM = this.createSegment99999Minus(this.volume, newValue);
            await this.showSegment(segP, [0.3, 0.7, 0.6], 0.5);
            await this.showSegment(segM, [0.1, 0.3, 0.7]);
        }

    }

    private repr: any = undefined;
    async load99999() {
        const entryId = 'emd-99999';
        const url = this.volumeServerRequestUrl('emdb', entryId, 0, [[-1000, -1000, -1000], [1000, 1000, 1000]], 10000000);
        // http://localhost:9000/v1/emdb/emd-99999/box/0/-10000/-10000/-10000/10000/10000/10000/10000000
        const { plugin } = this;

        await plugin.clear();

        const data = await plugin.builders.data.download({ url, isBinary: true }, { state: { isGhost: true } });
        const parsed = await plugin.dataFormats.get('dscif')!.parse(plugin, data);
        const volume: StateObjectSelector<PluginStateObject.Volume.Data> = parsed.volumes?.[0] ?? parsed.volume;
        const volumeData = volume.cell!.obj!.data;
        this.volume = volumeData;
        const repr = plugin.build();

        this.repr = repr
            .to(volume)
            .apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volumeData, {
                type: 'isosurface',
                typeParams: { alpha: 1.0, isoValue: Volume.IsoValue.relative(-0.55) },
                color: 'uniform',
                colorParams: { value: Color(0x224899) }
            }));

        await repr.commit();

        this.currentSegments = [];
        // const segP = this.createSegment99999Plus(volumeData, 0);
        // const segM = this.createSegment99999Minus(volumeData, -0.55);
        // await this.showSegment(segP, [0.3, 0.7, 0.1]);
        // await this.showSegment(segM, [0.1, 0.3, 0.7]);

        this.dataSource.next('99999');
    }


    splitEntryId(entryId: string){
        const PREFIX_TO_SOURCE: {[prefix: string]: string} = {'empiar': 'empiar', 'emd': 'emdb'};
        const [prefix, entry] = entryId.split('-');
        return {
            source: PREFIX_TO_SOURCE[prefix], 
            entryNumber: entry
        };
    }
    createEntryId(source: string, entryNumber: string|number){
        const SOURCE_TO_PREFIX: {[prefix: string]: string} = {'empiar': 'empiar', 'emdb': 'emd'};
        return `${SOURCE_TO_PREFIX[source]}-${entryNumber}`;
    }

}


const CreateTransformer = StateTransformer.builderFactory('cellstar');

const CreateVolume = CreateTransformer({
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