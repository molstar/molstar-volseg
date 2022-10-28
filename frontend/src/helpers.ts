import { StateBuilder, StateObjectSelector, StateTransform, StateTransformer } from 'molstar/lib/mol-state';
import { PluginStateObject } from 'molstar/lib/mol-plugin-state/objects';
import { Grid, Volume } from 'molstar/lib/mol-model/volume';
import { ParamDefinition as PD } from 'molstar/lib/mol-util/param-definition';
import { CustomProperties } from 'molstar/lib/mol-model/custom-property';
import { CIF, CifBlock } from 'molstar/lib/mol-io/reader/cif';
import { volumeFromDensityServerData } from 'molstar/lib/mol-model-formats/volume/density-server'
import { Tensor, Vec3 } from 'molstar/lib/mol-math/linear-algebra';
import { Box3D } from 'molstar/lib/mol-math/geometry';
import { CreateGroup } from 'molstar/lib/mol-plugin-state/transforms/misc';
import { setSubtreeVisibility } from 'molstar/lib/mol-plugin/behavior/static/state';

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



type Box = [number, number, number, number, number, number];

/** Represents a 3D box in integer coordinates. xFrom... is inclusive, xTo... is exclusive. */
namespace Box {
    export function create(xFrom: number, xTo: number, yFrom: number, yTo: number, zFrom: number, zTo: number): Box {
        return [xFrom, xTo, yFrom, yTo, zFrom, zTo];
    }
    export function expand(box: Box, expandFrom: number, expandTo: number): Box {
        const [xFrom, xTo, yFrom, yTo, zFrom, zTo] = box;
        return [xFrom - expandFrom, xTo + expandTo, yFrom - expandFrom, yTo + expandTo, zFrom - expandFrom, zTo + expandTo];
    }
    export function confine(box1: Box, box2: Box): Box {
        const [xFrom1, xTo1, yFrom1, yTo1, zFrom1, zTo1] = box1;
        const [xFrom2, xTo2, yFrom2, yTo2, zFrom2, zTo2] = box2;
        return [
            Math.max(xFrom1, xFrom2), Math.min(xTo1, xTo2),
            Math.max(yFrom1, yFrom2), Math.min(yTo1, yTo2),
            Math.max(zFrom1, zFrom2), Math.min(zTo1, zTo2)
        ];
    }
    export function cover(box1: Box, box2: Box): Box {
        const [xFrom1, xTo1, yFrom1, yTo1, zFrom1, zTo1] = box1;
        const [xFrom2, xTo2, yFrom2, yTo2, zFrom2, zTo2] = box2;
        return [
            Math.min(xFrom1, xFrom2), Math.max(xTo1, xTo2),
            Math.min(yFrom1, yFrom2), Math.max(yTo1, yTo2),
            Math.min(zFrom1, zFrom2), Math.max(zTo1, zTo2)
        ];
    }
    export function size(box: Box): [number, number, number] {
        const [xFrom, xTo, yFrom, yTo, zFrom, zTo] = box;
        return [xTo - xFrom, yTo - yFrom, zTo - zFrom];
    }
    export function origin(box: Box): [number, number, number] {
        const [xFrom, xTo, yFrom, yTo, zFrom, zTo] = box;
        return [xFrom, yFrom, zFrom];
    }
    export function log(name: string, box: Box): void {
        const [xFrom, xTo, yFrom, yTo, zFrom, zTo] = box;
        console.log(`Box ${name}: [${xFrom}:${xTo}, ${yFrom}:${yTo}, ${zFrom}:${zTo}], size: ${size(box)}`);
    }
    export function toFractional(box: Box, relativeTo: Box): Box3D {
        const [xFrom, xTo, yFrom, yTo, zFrom, zTo] = box;
        const [x0, y0, z0] = origin(relativeTo);
        const [sizeX, sizeY, sizeZ] = size(relativeTo);
        const min = Vec3.create((xFrom - x0) / sizeX, (yFrom - y0) / sizeY, (zFrom - z0) / sizeZ);
        const max = Vec3.create((xTo - x0) / sizeX, (yTo - y0) / sizeY, (zTo - z0) / sizeZ);
        return Box3D.create(min, max);
    }
    export function addPoint_InclusiveEnd(box: Box, x: number, y: number, z: number): void {
        if (x < box[0]) box[0] = x;
        if (x > box[1]) box[1] = x;
        if (y < box[2]) box[2] = y;
        if (y > box[3]) box[3] = y;
        if (z < box[4]) box[4] = z;
        if (z > box[5]) box[5] = z;
    }
    export function equal(box1: Box, box2: Box): boolean {
        return box1.every((value, i) => value === box2[i]);
    }
}

export class LatticeSegmentation {
    private segments: number[];
    private sets: number[];
    /** Maps setId to a set of segmentIds*/
    private segmentMap: Map<number, Set<number>>; // computations with objects might be actually faster than with Maps and Sets?
    /** Maps segmentId to a set of setIds*/
    private inverseSegmentMap: Map<number, Set<number>>;
    private grid: Grid;

    private constructor(segmentationDataBlock: CifBlock, grid: Grid) {
        const segmentationValues = segmentationDataBlock!.categories['segmentation_data_3d'].getField('values')?.toIntArray()!;
        this.segmentMap = LatticeSegmentation.makeSegmentMap(segmentationDataBlock);
        this.inverseSegmentMap = LatticeSegmentation.invertMultimap(this.segmentMap);
        this.segments = Array.from(this.inverseSegmentMap.keys());
        this.sets = Array.from(this.segmentMap.keys());
        this.grid = grid;
        this.grid.cells.data = Tensor.Data1(segmentationValues);
    }

    public static async fromCifBlock(segmentationDataBlock: CifBlock) {
        const densityServerCif = CIF.schema.densityServer(segmentationDataBlock);
        // console.log('dscif', densityServerCif);
        const volume = await volumeFromDensityServerData(densityServerCif).run();
        // console.log('volume', volume);
        const grid = volume.grid;
        return new LatticeSegmentation(segmentationDataBlock, grid);
    }

    public createSegment_old(segId: number): Volume {
        // console.time('createSegment_old');
        const n = this.grid.cells.data.length;
        const newData = new Float32Array(n);

        for (let i = 0; i < n; i++) {
            newData[i] = this.segmentMap.get(this.grid.cells.data[i])?.has(segId) ? 1 : 0;
        }

        const result: Volume = {
            sourceData: { kind: 'custom', name: 'test', data: newData as any },
            customProperties: new CustomProperties(),
            _propertyData: {},
            grid: {
                ...this.grid,
                // stats: { min: 0, max: 1, mean: newMean, sigma: arrayRms(newData) },
                stats: { min: 0, max: 1, mean: 0, sigma: 1 },
                cells: {
                    ...this.grid.cells,
                    data: newData as any,
                }
            }
        };
        // console.timeEnd('createSegment_old');
        return result;
    }

    public createSegment(segId: number): Volume {
        const { space, data }: Tensor = this.grid.cells;
        const [nx, ny, nz] = space.dimensions;
        const axisOrder = [...space.axisOrderSlowToFast];
        const get = space.get;
        const cell = Box.create(0, nx, 0, ny, 0, nz);

        const EXPAND_START = 2; // We need to add 2 layers of zeros, probably because of a bug in GPU marching cubes implementation
        const EXPAND_END = 1;
        let bbox = this.getSegmentBoundingBoxes()[segId];
        // if (!Box.equal(bbox, this.getBoundingBox(segId))) throw new Error('Assertion Error');
        bbox = Box.expand(bbox, EXPAND_START, EXPAND_END);
        bbox = Box.confine(bbox, cell);
        const [ox, oy, oz] = Box.origin(bbox);
        const [mx, my, mz] = Box.size(bbox);
        // n, i refer to original box; m, j to the new box

        const newSpace = Tensor.Space([mx, my, mz], axisOrder, Uint8Array);
        const newTensor = Tensor.create(newSpace, newSpace.create());
        const newData = newTensor.data;
        const newSet = newSpace.set;

        const sets = this.inverseSegmentMap.get(segId);
        if (!sets) throw new Error(`This LatticeSegmentation does not contain segment ${segId}`);

        for (let jz = 0; jz < mz; jz++) {
            for (let jy = 0; jy < my; jy++) {
                for (let jx = 0; jx < mx; jx++) {
                    // Iterating in ZYX order is faster (probably fewer cache misses)
                    const setId = get(data, ox + jx, oy + jy, oz + jz);
                    const value = sets.has(setId) ? 1 : 0;
                    newSet(newData, jx, jy, jz, value);
                }
            }
        }

        const transform = this.grid.transform;
        let newTransform: Grid.Transform;
        if (transform.kind === 'matrix') {
            throw new Error('Not implemented for transform of kind "matrix"'); // TODO ask if this is really needed
        } else if (transform.kind === 'spacegroup') {
            const newFractionalBox = Box.toFractional(bbox, cell);
            Vec3.add(newFractionalBox.min, newFractionalBox.min, transform.fractionalBox.min);
            Vec3.add(newFractionalBox.max, newFractionalBox.max, transform.fractionalBox.min);
            newTransform = { ...transform, fractionalBox: newFractionalBox };
        } else {
            throw new Error(`Unknown transform kind: ${transform}`);
        }
        const result = {
            sourceData: { kind: 'custom', name: 'test', data: newTensor.data as any },
            customProperties: new CustomProperties(),
            _propertyData: {},
            grid: {
                stats: { min: 0, max: 1, mean: 0, sigma: 1 },
                cells: newTensor,
                transform: newTransform,
            }
        };
        return result;
    }

    private getBoundingBox(segId: number): Box {
        const { space, data }: Tensor = this.grid.cells;
        const [nx, ny, nz] = space.dimensions;
        const get = space.get;

        let minX = nx, minY = ny, minZ = nz;
        let maxX = -1, maxY = -1, maxZ = -1;

        const sets = this.inverseSegmentMap.get(segId);
        if (!sets) throw new Error(`This LatticeSegmentation does not contain segment ${segId}`);

        for (let iz = 0; iz < nz; iz++) {
            for (let iy = 0; iy < ny; iy++) {
                for (let ix = 0; ix < nx; ix++) {
                    // Iterating in ZYX order is faster (probably fewer cache misses)
                    const setId = get(data, ix, iy, iz);
                    if (sets.has(setId)) {
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
        if (maxX === -1) { // segment contains no voxels
            return Box.create(0, 1, 0, 1, 0, 1);
        }
        const box = Box.create(minX, maxX + 1, minY, maxY + 1, minZ, maxZ + 1);
        return box;
    }

    private static _getSegmentBoundingBoxes(self: LatticeSegmentation) {
        const { space, data }: Tensor = self.grid.cells;
        const [nx, ny, nz] = space.dimensions;
        const get = space.get;

        const setBoxes: { [setId: number]: Box } = {}; // with object this is faster than with Map
        self.sets.forEach(setId => setBoxes[setId] = Box.create(nx, -1, ny, -1, nz, -1));

        for (let iz = 0; iz < nz; iz++) {
            for (let iy = 0; iy < ny; iy++) {
                for (let ix = 0; ix < nx; ix++) {
                    // Iterating in ZYX order is faster (probably fewer cache misses)
                    const setId = get(data, ix, iy, iz);
                    Box.addPoint_InclusiveEnd(setBoxes[setId], ix, iy, iz);
                }
            }
        }

        const segmentBoxes: { [segmentId: number]: Box } = {};
        self.segments.forEach(segmentId => segmentBoxes[segmentId] = Box.create(nx, -1, ny, -1, nz, -1));
        self.inverseSegmentMap.forEach((setIds, segmentId) => {
            setIds.forEach(setId => {
                segmentBoxes[segmentId] = Box.cover(segmentBoxes[segmentId], setBoxes[setId]);
            });
        });

        for (const segmentId in segmentBoxes) {
            if (segmentBoxes[segmentId][5] === -1) { // segment's box left unchanged -> contains no voxels
                segmentBoxes[segmentId] = Box.create(0, 1, 0, 1, 0, 1);
            } else {
                segmentBoxes[segmentId] = Box.expand(segmentBoxes[segmentId], 0, 1); // inclusive end -> exclusive end
            }
        }
        return segmentBoxes;
    }
    private getSegmentBoundingBoxes = lazyGetter(() => LatticeSegmentation._getSegmentBoundingBoxes(this));

    private static invertMultimap<K, V>(map: Map<K, Set<V>>): Map<V, Set<K>> {
        const inverted = new Map<V, Set<K>>();
        map.forEach((values, key) => {
            values.forEach(value => {
                if (!inverted.has(value)) inverted.set(value, new Set<K>());
                inverted.get(value)?.add(key);
            });
        });
        return inverted;
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

    public benchmark(segId: number) {
        const N = 100;

        console.time(`createSegment ${segId} ${N}x`);
        for (let i = 0; i < N; i++) {
            this.getSegmentBoundingBoxes = lazyGetter(() => LatticeSegmentation._getSegmentBoundingBoxes(this));
            this.createSegment(segId);
        }
        console.timeEnd(`createSegment ${segId} ${N}x`);
    }
    public benchmarkAll() {
        const N = 100;
        const segments: number[] = [];
        this.inverseSegmentMap.forEach((v, k) => segments.push(k));

        console.time(`createSegment ALL ${N}x`);
        for (let i = 0; i < N; i++) {
            this.getSegmentBoundingBoxes = lazyGetter(() => LatticeSegmentation._getSegmentBoundingBoxes(this));
            for (const segId of segments) {
                this.createSegment(segId);
            }
        }
        console.timeEnd(`createSegment ALL ${N}x`);
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


export function lazyGetter<T>(getter: () => T) {
    let value: T | undefined = undefined;
    return () => {
        if (value === undefined) value = getter();
        return value;
    };
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
    public groupLabel?: string;
    private groupOptions?: Partial<StateTransform.Options>;
    private group?: StateObjectSelector;
    private nodes: { [key: string]: StateObjectSelector };

    constructor(groupName?: string, groupOptions?: Partial<StateTransform.Options>) {
        this.groupLabel = groupName;
        this.group = undefined;
        this.nodes = {};
    }

    private static nodeExists(node: StateObjectSelector): boolean {
        try {
            return node.checkValid();
        } catch {
            return false;
        }
    }

    public getGroup(update: StateBuilder.Root, parent?: StateObjectSelector): StateObjectSelector {
        if (!this.groupLabel) {
            return parent ?? update.toRoot().selector;
        }
        if (this.group && NodeManager.nodeExists(this.group)) {
            return this.group;
        }
        const to = parent ? update.to(parent) : update.toRoot();
        this.group = to.apply(CreateGroup, { label: this.groupLabel }, this.groupOptions).selector;
        return this.group;
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