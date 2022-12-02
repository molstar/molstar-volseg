import { CustomProperties } from 'molstar/lib/mol-model/custom-property';
import { Volume } from 'molstar/lib/mol-model/volume';
import { createVolumeRepresentationParams } from 'molstar/lib/mol-plugin-state/helpers/volume-representation-params';
import { PluginStateObject } from 'molstar/lib/mol-plugin-state/objects';
import { StateTransforms } from 'molstar/lib/mol-plugin-state/transforms';
import { StateObjectSelector } from 'molstar/lib/mol-state';
import { Asset } from 'molstar/lib/mol-util/assets';
import { Color } from 'molstar/lib/mol-util/color';
import { ColorNames } from 'molstar/lib/mol-util/color/names';
import { PluginUIContext } from 'molstar/lib/mol-plugin-ui/context';
import { UUID } from 'molstar/lib/mol-util';

import * as MeshExamples from '../mesh-extension/examples';
import { type Metadata, Segment } from '../volume-api-client-lib/data';
import * as ExternalAPIs from './external-api';
import { CreateVolume, Debugging, ExampleType, MetadataUtils, NodeManager, splitEntryId } from './helpers';
import { LatticeSegmentation } from './lattice-segmentation';
import { AppModel, API2 } from './model';


const USE_GHOST_NODES = false;
const DEFAULT_MESH_DETAIL: number | null = 5;  // null means worst
const MESH_HIDE_BACKGROUND_EMPIAR_10070 = true;


interface Example {
    exampleType: ExampleType,
    defaultEntryId: string,
    action: (entryId: string) => any,
}


export class Session {
    constructor(
        private id: UUID,
        private model: AppModel,
        private plugin: PluginUIContext
    ) { }

    private metadata?: Metadata;
    private volume?: Volume;
    private segmentation?: LatticeSegmentation;

    private currentSegments: any[] = [];
    private volumeRepr: any;

    private segmentationNodeMgr = new NodeManager('Segmentation');
    private pdbModelNodeMgr = new NodeManager();
    private meshSegmentNodeMgr = new NodeManager();


    private readonly exampleEmdb: Example = {
        exampleType: 'emdb',
        defaultEntryId: 'emd-1832',
        action: async (entryId) => {
            // const isoLevel = { kind: 'relative', value: 2.73};
            this.metadata = await this.initMetadata(entryId);
            const isoLevel = await ExternalAPIs.getIsovalue(entryId);
            const source = splitEntryId(entryId).source as 'empiar' | 'emdb';
            const segmentationId = 0
            const { plugin } = this;

            const MAX_VOXELS = 10 ** 7;

            // VOLUME
            const volumeUrl = API2.volumeUrl(source, entryId, null, MAX_VOXELS);
            const volumeDataNode = await plugin.builders.data.download({ url: volumeUrl, isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
            const parsed = await plugin.dataFormats.get('dscif')!.parse(plugin, volumeDataNode, { entryId });
            const volume: StateObjectSelector<PluginStateObject.Volume.Data> = parsed.volumes?.[0] ?? parsed.volume;
            const volumeData = volume.cell!.obj!.data;
            this.volume = volumeData;

            // LATTICE SEGMENTATION
            const latticeUrl = API2.latticeUrl(source, entryId, segmentationId, null, MAX_VOXELS);
            const latticeDataNode = await plugin.builders.data.download({ url: latticeUrl, isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
            const cif = await plugin.build().to(latticeDataNode).apply(StateTransforms.Data.ParseCif).commit();
            // Debugging.logCifOverview(cif.data!, latticeUrl);
            const latticeBlock = cif.data!.blocks.find(b => b.header === 'SEGMENTATION_DATA');

            this.segmentation = await LatticeSegmentation.fromCifBlock(latticeBlock!);

            const repr = plugin.build();

            repr
                .to(volume)
                .apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volumeData, {
                    type: 'isosurface',
                    typeParams: { alpha: 0.2, isoValue: Volume.adjustedIsoValue(volumeData, isoLevel.value, isoLevel.kind), tryUseGpu: false  },
                    color: 'uniform',
                    colorParams: { value: Color(0x121212) }
                }));

            await repr.commit();

            await this.showSegments(this.metadata.annotation.segment_list);
        }
    }

    private readonly exampleBioimage: Example = {
        exampleType: 'bioimage',
        defaultEntryId: 'emd-99999',
        action: async (entryId) => {
            this.metadata = await this.initMetadata(entryId);
            const url = API2.volumeUrl('emdb', entryId, null, 10 ** 7);
            // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 0], [70_000, 69_000, 1_200]], 10**2);
            // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 0], [80_000, 65_600, 1_600]], 10**2); // 1025 voxels
            // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 0], [76_000, 68_000, 800]], 10**2); // 1023 voxels
            // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 0], [70_400, 69_600, 1_200]], 10**2); // 1020 voxels
            // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 400], [67_600, 67_600, 4_000]], 10**2); // 1000 voxels
            // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 0], [79_600, 65_600, 1_600]], 10**2); // 1000 voxels
            // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 400], [108_000, 64_800, 1200]], 10**2); // 999 voxels
            // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 400], [78_400, 67_200, 1_200]], 10**2); // 999 voxels
            // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 0], [69_600, 68_000, 2_000]], 10**2); // 900 voxels

            const data = await this.plugin.builders.data.download({ url, isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
            const parsed = await this.plugin.dataFormats.get('dscif')!.parse(this.plugin, data);
            // const cif = await this.plugin.build().to(data).apply(StateTransforms.Data.ParseCif).commit(); // DEBUG
            // Debugging.logCifOverview(cif.data!); // DEBUG
            // Debugging.logCifOverview(parsed); // DEBUG
            const volume: StateObjectSelector<PluginStateObject.Volume.Data> = parsed.volumes?.[0] ?? parsed.volume;
            const volumeData = volume.cell!.obj!.data;
            this.volume = volumeData;
            // console.log('volume.grid:', volumeData.grid); // DEBUG

            this.volumeRepr = this.plugin.build()
                .to(volume)
                .apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volumeData, {
                    type: 'isosurface',
                    typeParams: { alpha: 1.0, isoValue: Volume.IsoValue.relative(-0.55), tryUseGpu: false  },
                    color: 'uniform',
                    colorParams: { value: Color(0x224899) }
                }));
            await this.volumeRepr.commit();

            // const segP = this.createSegment99999Plus(volumeData, 0);
            // const segM = this.createSegment99999Minus(volumeData, -0.55);
            // await this.showSegment(segP, [0.3, 0.7, 0.1]);
            // await this.showSegment(segM, [0.1, 0.3, 0.7]);

        }
    }

    private readonly exampleMeshes: Example = {
        exampleType: 'meshes',
        defaultEntryId: 'empiar-10070',
        action: async (entryId) => {
            this.metadata = await this.initMetadata(entryId);
            if (entryId === 'empiar-10070' && MESH_HIDE_BACKGROUND_EMPIAR_10070) {
                const bgSegments = [13, 15];
                MetadataUtils.dropSegments(this.metadata, bgSegments);
            }

            await this.showMeshSegments(this.metadata.annotation.segment_list, entryId);
        }
    }

    private readonly exampleMeshStreaming: Example = {
        exampleType: 'meshStreaming',
        defaultEntryId: 'empiar-10070',
        action: async (entryId) => {
            this.metadata = await this.initMetadata(entryId);
            const source = splitEntryId(entryId).source as 'empiar' | 'emdb';
            await MeshExamples.runMeshStreamingExample(this.plugin, source, entryId, API2.volumeServerUrl);
        }
    }

    private readonly exampleAuto: Example = {
        exampleType: 'auto',
        defaultEntryId: 'emd-1832',
        action: async (entryId) => {
            this.metadata = await this.initMetadata(entryId);
            const source = splitEntryId(entryId).source as 'empiar' | 'emdb';
            const isoLevelPromise = ExternalAPIs.getIsovalue(entryId);
            const pdbsPromise = ExternalAPIs.getPdbIdsForEmdbEntry(entryId);

            const hasVolumes = this.metadata.grid.volumes.volume_downsamplings.length > 0;
            const hasLattices = this.metadata.grid.segmentation_lattices.segmentation_lattice_ids.length > 0;
            const hasMeshes = this.metadata.grid.segmentation_meshes.mesh_component_numbers.segment_ids !== undefined;

            // const A = 10 ** 4;
            // const BOX: [[number, number, number], [number, number, number]] = [[-A, -A, -A], [A, A, A]];
            const BOX = null;
            const MAX_VOXELS = 10 ** 7;

            // // DEBUG
            // const debugVolumeInfo = false;
            // if (debugVolumeInfo) {
            //     const url = API2.volumeInfoUrl(source, entryId);
            //     const data = await this.plugin.builders.data.download({ url, isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
            //     const cif = await this.plugin.build().to(data).apply(StateTransforms.Data.ParseCif).commit();
            //     Debugging.logCifOverview(cif.data!, url); // TODO when could cif.data be undefined?
            // }

            // // DEBUG
            // const debugMeshesBcif = false;
            // const debugSegment = 1;
            // const debugDetail = 10;
            // if (debugMeshesBcif) {
            //     const url = API2.meshUrl_Bcif(source, entryId, debugSegment, debugDetail);
            //     const data = await this.plugin.builders.data.download({ url, isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
            //     const cif = await this.plugin.build().to(data).apply(StateTransforms.Data.ParseCif).commit();
            //     Debugging.logCifOverview(cif.data!, url); // TODO when could cif.data be undefined?
            // }

            if (hasVolumes) {
                const url = API2.volumeUrl(source, entryId, BOX, MAX_VOXELS);
                const data = await this.plugin.builders.data.download({ url, isBinary: true, label: `Volume Data: ${url}` }, { state: { isGhost: USE_GHOST_NODES } });
                // const cif = await this.plugin.build().to(data).apply(StateTransforms.Data.ParseCif).commit(); Debugging.logCifOverview(cif.data!); // DEBUG
                const parsed = await this.plugin.dataFormats.get('dscif')!.parse(this.plugin, data, { entryId });
                const volume: StateObjectSelector<PluginStateObject.Volume.Data> = parsed.volumes?.[0] ?? parsed.volume;
                let volumeData = volume.cell!.obj!.data;
                this.volume = volumeData;
                // const isoLevel = { kind: 'relative', value: 2.73}; // rel 2.73 (abs 0.42) is OK for emd-1832
                const isoLevel = await isoLevelPromise;
                await this.plugin.build()
                    .to(volume)
                    .apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volumeData, {
                        type: 'isosurface',
                        typeParams: { alpha: 0.2, isoValue: Volume.adjustedIsoValue(volumeData, isoLevel.value, isoLevel.kind), tryUseGpu: false  },
                        color: 'uniform',
                        colorParams: { value: Color(0x121212) }
                    }))
                    .commit();
            }
            if (hasLattices) {
                const url = API2.latticeUrl(source, entryId, 0, BOX, MAX_VOXELS);
                const data = await this.plugin.builders.data.download({ url, isBinary: true, label: `Segmentation Data: ${url}` }, { state: { isGhost: USE_GHOST_NODES } });
                const cif = await this.plugin.build().to(data).apply(StateTransforms.Data.ParseCif).commit();
                // Debugging.logCifOverview(cif.data!, url); // TODO when could cif.data be undefined?
                const latticeBlock = cif.data!.blocks.find(b => b.header === 'SEGMENTATION_DATA');
                if (latticeBlock) {
                    this.segmentation = await LatticeSegmentation.fromCifBlock(latticeBlock);
                    await this.showSegments(this.metadata.annotation.segment_list);
                } else {
                    console.log('WARNING: Block SEGMENTATION_DATA is missing. Not showing segmentations.');
                }
            }
            if (hasMeshes) {
                await MeshExamples.runMeshStreamingExample(this.plugin, source, entryId, API2.volumeServerUrl);
            }

            this.model.pdbs.nextWithinSession(await pdbsPromise, this.id);
        }
    }

    public readonly examples: { [name in ExampleType]: Example } = {
        emdb: this.exampleEmdb,
        bioimage: this.exampleBioimage,
        meshes: this.exampleMeshes,
        meshStreaming: this.exampleMeshStreaming,
        auto: this.exampleAuto,
    }

    private async initMetadata(entryId: string) {
        if (!this.metadata) {
            const source = splitEntryId(entryId).source as 'empiar' | 'emdb';
            this.metadata = await API2.getMetadata(source, entryId);
            this.model.annotation.nextWithinSession(this.metadata.annotation, this.id);
        }
        return this.metadata;
    }

    async loadPdb(pdbId: string) {
        const url = `https://www.ebi.ac.uk/pdbe/entry-files/download/${pdbId}.bcif`;
        return await this.loadPdbStructureFromBcif(url, { dataLabel: `PDB Data: ${url}` });
    }

    async loadPdbStructureFromBcif(url: string, options?: { dataLabel?: string }) {
        const urlAsset = Asset.getUrlAsset(this.plugin.managers.asset, url);
        const asset = await this.plugin.runTask(this.plugin.managers.asset.resolve(urlAsset, 'binary'));
        const data = asset.data;

        const dataNode = await this.plugin.builders.data.rawData({ data, label: options?.dataLabel });
        const trajectoryNode = await this.plugin.builders.structure.parseTrajectory(dataNode, 'mmcif');
        await this.plugin.builders.structure.hierarchy.applyPreset(trajectoryNode, 'default');
        return dataNode;
    }

    async showPdb(pdbId: string | undefined) {
        this.model.status.nextWithinSession('loading', this.id);
        try {
            this.pdbModelNodeMgr.hideAllNodes();
            if (pdbId) {
                await this.pdbModelNodeMgr.showNode(pdbId, async () => await this.loadPdb(pdbId));
            }
            this.model.currentPdb.nextWithinSession(pdbId, this.id);
            this.model.status.nextWithinSession('ready', this.id);
        } catch (ex) {
            this.model.status.nextWithinSession('error', this.id);
            throw ex;
        }
    }

    /** Make visible the specified set of lattice segments */
    async showSegments(segments: Segment[]) {
        if (segments.length === 1) {
            this.model.currentSegment.nextWithinSession(segments[0], this.id);
        } else {
            this.model.currentSegment.nextWithinSession(undefined, this.id);
        }

        const update = this.plugin.build();
        const group = this.segmentationNodeMgr.getGroup(update);

        this.segmentationNodeMgr.hideAllNodes();

        for (const seg of segments) {
            this.segmentationNodeMgr.showNode(seg.id.toString(), () => {
                const volume = this.segmentation?.createSegment(seg.id);
                Volume.PickingGranularity.set(volume!, 'volume');
                const volumeNode = update.to(group).apply(CreateVolume, { volume, label: `Segment ${seg.id}`, description: seg.biological_annotation?.name }, { state: { isCollapsed: true } });

                volumeNode.apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volume, {
                    type: 'isosurface',
                    typeParams: { alpha: 1, isoValue: Volume.IsoValue.absolute(0.95), tryUseGpu: false },
                    color: 'uniform',
                    colorParams: { value: Color.fromNormalizedArray(seg.colour, 0) }
                }));
                return volumeNode.selector;
            });
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

    /** Make visible the specified set of mesh segments */
    async showMeshSegments(segments: Segment[], entryId: string) {
        if (segments.length === 1) {
            this.model.currentSegment.nextWithinSession(segments[0], this.id);
        } else {
            this.model.currentSegment.nextWithinSession(undefined, this.id);
        }

        this.meshSegmentNodeMgr.hideAllNodes();

        for (const seg of segments) {
            await this.meshSegmentNodeMgr.showNode(seg.id.toString(), async () => {
                const detail = MetadataUtils.getSufficientDetail(this.metadata!, seg.id, DEFAULT_MESH_DETAIL);
                const color = seg.colour.length >= 3 ? Color.fromNormalizedArray(seg.colour, 0) : ColorNames.gray;
                return await MeshExamples.createMeshFromUrl(this.plugin, API2.meshUrl_Bcif(splitEntryId(entryId).source, entryId, seg.id, detail), seg.id, detail, true, false, color);
            });
        }
    }

    private createFakeSegment(volume: Volume, level: number): Volume {
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

    private createSegment99999Plus(volume: Volume, threshold: number): Volume {
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

    private createSegment99999Minus(volume: Volume, threshold: number): Volume {
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

    private async showSegment(volume: Volume, color: number[], opacity = 1) {
        const update = this.plugin.build();
        const root = update.toRoot().apply(CreateVolume, { volume });

        const seg = root.apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volume, {
            type: 'isosurface',
            typeParams: { alpha: opacity, isoValue: Volume.IsoValue.absolute(0.95), transparentBackfaces: 'off', doubleSided: false, flatShaded: true, tryUseGpu: false  },
            color: 'uniform',
            colorParams: { value: Color.fromNormalizedArray(color, 0) }
        }));

        this.currentSegments.push(seg.selector);

        await update.commit();
    }

    /** Change isovalue for existing volume representation (in Bioimage example) */
    async setIsoValue(newValue: number, showSegmentation: boolean) {
        if (!this.volumeRepr) return;

        const { plugin } = this;
        await plugin.build().to(this.volumeRepr).update(createVolumeRepresentationParams(this.plugin, this.volume, {
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
            const segP = this.createSegment99999Plus(this.volume!, -0.35);
            const segM = this.createSegment99999Minus(this.volume!, newValue);
            await this.showSegment(segP, [0.3, 0.7, 0.6], 0.5);
            await this.showSegment(segM, [0.1, 0.3, 0.7]);
        }

    }
}
