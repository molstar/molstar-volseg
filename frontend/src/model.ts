import { CifFile } from 'molstar/lib/mol-io/reader/cif';
import { CustomProperties } from 'molstar/lib/mol-model/custom-property';
import { Volume } from 'molstar/lib/mol-model/volume';
import { createVolumeRepresentationParams } from 'molstar/lib/mol-plugin-state/helpers/volume-representation-params';
import { PluginStateObject } from 'molstar/lib/mol-plugin-state/objects';
import { StateTransforms } from 'molstar/lib/mol-plugin-state/transforms';
import { CreateGroup } from 'molstar/lib/mol-plugin-state/transforms/misc';
import { PluginUIContext } from 'molstar/lib/mol-plugin-ui/context';
import { createPluginUI } from 'molstar/lib/mol-plugin-ui/react18';
import { DefaultPluginUISpec } from 'molstar/lib/mol-plugin-ui/spec';
import { setSubtreeVisibility } from 'molstar/lib/mol-plugin/behavior/static/state';
import { PluginConfig } from 'molstar/lib/mol-plugin/config';
import { StateBuilder, StateObjectSelector, StateTransform } from 'molstar/lib/mol-state';
import { Asset } from 'molstar/lib/mol-util/assets';
import { Color } from 'molstar/lib/mol-util/color';
import { BehaviorSubject } from 'rxjs';

import { CreateVolume, ExampleType, LatticeSegmentation, MetadataUtils, UrlFragmentInfo } from './helpers';
import * as MeshExamples from './mesh-extension/examples';
import { ColorNames } from './mesh-extension/molstar-lib-imports';
import { Annotation, Segment, type Metadata } from './volume-api-client-lib/data';
import { VolumeApiV1, VolumeApiV2 } from './volume-api-client-lib/volume-api';


const DEFAULT_DETAIL: number | null = null;  // null means worst

const USE_GHOST_NODES = false;

const API2 = new VolumeApiV2();


export class AppModel {
    public entryId = new BehaviorSubject<string>('');
    public annotation = new BehaviorSubject<Annotation | undefined>(undefined);
    public currentSegment = new BehaviorSubject<Segment | undefined>(undefined);
    public pdbs = new BehaviorSubject<string[]>([]);
    public currentPdb = new BehaviorSubject<string | undefined>(undefined);
    public error = new BehaviorSubject<any>(undefined);
    public exampleType = new BehaviorSubject<ExampleType>('');
    public status = new BehaviorSubject<'ready' | 'loading' | 'error'>('ready');

    private plugin: PluginUIContext = undefined as any;

    private volume?: Volume;
    private segmentationGroup?: StateObjectSelector = undefined;
    private segmentationNodes = [] as StateObjectSelector[];
    private pdbModelNodes: {[pdb: string]: StateObjectSelector} = {};

    private segmentation?: LatticeSegmentation;

    private metadata?: Metadata = undefined;
    private meshSegmentNodes: { [segid: number]: StateObjectSelector } = {};

    private currentSegments: any[] = [];
    private volumeRepr: any = undefined;



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

        // this.testApiV2();
        // return;

        const fragment = UrlFragmentInfo.get();
        switch (fragment.example) {
            case 'xEmdb':
                setTimeout(() => this.loadExampleEmdb(fragment.entry), 50);
                break;
            case 'xBioimage':
                setTimeout(() => this.loadExampleBioimage(fragment.entry), 50);
                break;
            case 'xMeshes':
                setTimeout(() => this.loadExampleMeshes(fragment.entry), 50);
                break;
            case 'xMeshStreaming':
                setTimeout(() => this.loadExampleMeshStreaming(fragment.entry), 50);
                break;
            case 'xAuto':
                setTimeout(() => this.loadExampleAuto(fragment.entry), 50);
                break;
            default:
                setTimeout(() => this.loadExampleAuto(fragment.entry), 50);
                break;
        }
    }

    async testApiV2() {
        const A = 10 ** 5;
        const BOX: [[number, number, number], [number, number, number]] = [[-A, -A, -A], [A, A, A]];
        const MAX_VOXELS = 10 ** 7;
        const urls: { [name: string]: string } = {
            'VOLUME BOX EMD-1832': API2.volumeUrl('emdb', 'emd-1832', BOX, MAX_VOXELS),
            'LATTICE BOX EMD-1832': API2.latticeUrl('emdb', 'emd-1832', 0, BOX, MAX_VOXELS),
            'VOLUME CELL EMD-1832': API2.volumeUrl('emdb', 'emd-1832', null, MAX_VOXELS),
            'LATTICE CELL EMD-1832': API2.latticeUrl('emdb', 'emd-1832', 0, null, MAX_VOXELS),
            'VOLUME BOX EMPIAR-10070': API2.volumeUrl('empiar', 'empiar-10070', BOX, MAX_VOXELS),
            'LATTICE BOX EMPIAR-10070': API2.latticeUrl('empiar', 'empiar-10070', 0, BOX, MAX_VOXELS),
            'VOLUME CELL EMPIAR-10070': API2.volumeUrl('empiar', 'empiar-10070', null, MAX_VOXELS),
            'LATTICE CELL EMPIAR-10070': API2.latticeUrl('empiar', 'empiar-10070', 0, null, MAX_VOXELS),
            // 'VOLUME CELL EMD-1832': API2.volumeUrl('emdb', 'emd-1832', null, MAX_VOXELS),
            // 'VOLUME CELL EMD-1832 EBI': 'https://www.ebi.ac.uk/pdbe/densities/emd/emd-1832/cell?detail=5',
            // 'VOLUME CELL EMD-1547': API2.volumeUrl('emdb', 'emd-1547', null, MAX_VOXELS),
            // 'VOLUME CELL EMD-1547 EBI': 'https://www.ebi.ac.uk/pdbe/densities/emd/emd-1547/cell?detail=5',
            // 'VOLUME CELL EMD-1181': API2.volumeUrl('emdb', 'emd-1181', null, MAX_VOXELS),
            // 'VOLUME CELL EMD-1181 EBI': 'https://www.ebi.ac.uk/pdbe/densities/emd/emd-1181/cell?detail=5',
        };
        for (const name in urls) {
            console.log(`\n<<< ${name} >>>`);
            console.log(urls[name]);
            try {
                const data = await this.plugin.builders.data.download({ url: urls[name], isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
                const cif = await this.plugin.build().to(data).apply(StateTransforms.Data.ParseCif).commit();
                AppModel.logCifOverview(cif.data!, urls[name]);
                await this.testVolumeBbox(urls[name], 1.0);
            } catch (err) {
                console.error('Failed', err);
            }
        }
    }

    async testVolumeBbox(url: string, isoValue: number) {
        const volumeDataNode = await this.plugin.builders.data.download({ url: url, isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
        const parsed = await this.plugin.dataFormats.get('dscif')!.parse(this.plugin, volumeDataNode, { entryId: url });
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

    async loadExampleEmdb(entryId: string = 'emd-1832') {
        console.time('Load example');
        // const isoLevel = { kind: 'relative', value: 2.73};
        const isoLevel = await AppModel.getIsovalue(entryId);
        const source = AppModel.splitEntryId(entryId).source as 'empiar' | 'emdb';
        // const url = `https://maps.rcsb.org/em/${entryId}/cell?detail=6`;
        const segmentationId = 0
        const { plugin } = this;

        await plugin.clear();

        this.metadata = await API2.getMetadata(source, entryId);
        console.log('annotation:', this.metadata.annotation);

        const MAX_VOXELS = 100000000;
        // const MAX_VOXELS = 1000; // debug

        // VOLUME
        const volumeUrl = API2.volumeUrl(source, entryId, [[-1000, -1000, -1000], [1000, 1000, 1000]], MAX_VOXELS);
        const volumeDataNode = await plugin.builders.data.download({ url: volumeUrl, isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
        const parsed = await plugin.dataFormats.get('dscif')!.parse(plugin, volumeDataNode, { entryId });
        const volume: StateObjectSelector<PluginStateObject.Volume.Data> = parsed.volumes?.[0] ?? parsed.volume;
        const volumeData = volume.cell!.obj!.data;
        this.volume = volumeData;

        // LATTICE SEGMENTATION
        const latticeUrl = API2.latticeUrl(source, entryId, segmentationId, [[-1000, -1000, -1000], [1000, 1000, 1000]], MAX_VOXELS);
        const latticeDataNode = await plugin.builders.data.download({ url: latticeUrl, isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
        const cif = await plugin.build().to(latticeDataNode).apply(StateTransforms.Data.ParseCif).commit();
        AppModel.logCifOverview(cif.data!, latticeUrl);
        const latticeBlock = cif.data!.blocks.find(b => b.header === 'SEGMENTATION_DATA');

        this.entryId.next(entryId);
        this.annotation.next(this.metadata.annotation);
        this.segmentation = await LatticeSegmentation.fromCifBlock(latticeBlock!);

        const repr = plugin.build();

        repr
            .to(volume)
            .apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volumeData, {
                type: 'isosurface',
                typeParams: { alpha: 0.2, isoValue: Volume.adjustedIsoValue(volumeData, isoLevel.value, isoLevel.kind) },
                color: 'uniform',
                colorParams: { value: Color(0x121212) }
            }));

        await repr.commit();

        await this.showSegments(this.metadata.annotation.segment_list);

        UrlFragmentInfo.set({ example: 'xEmdb', entry: entryId });
        this.exampleType.next('xEmdb');
        console.timeEnd('Load example');
    }

    async loadExampleBioimage(entryId: string = 'emd-99999') {
        console.time('Load example');
        const url = API2.volumeUrl('emdb', entryId, null, 10**7);
        // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 0], [70_000, 69_000, 1_200]], 10**2);
        // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 0], [80_000, 65_600, 1_600]], 10**2); // 1025 voxels
        // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 0], [76_000, 68_000, 800]], 10**2); // 1023 voxels
        // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 0], [70_400, 69_600, 1_200]], 10**2); // 1020 voxels
        // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 400], [67_600, 67_600, 4_000]], 10**2); // 1000 voxels
        // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 0], [79_600, 65_600, 1_600]], 10**2); // 1000 voxels
        // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 400], [108_000, 64_800, 1200]], 10**2); // 999 voxels
        // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 400], [78_400, 67_200, 1_200]], 10**2); // 999 voxels
        // const url = API2.volumeUrl('emdb', entryId, [[64_000, 64_000, 0], [69_600, 68_000, 2_000]], 10**2); // 900 voxels

        const { plugin } = this;

        await plugin.clear();

        const data = await plugin.builders.data.download({ url, isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
        const parsed = await plugin.dataFormats.get('dscif')!.parse(plugin, data);
        const cif = await this.plugin.build().to(data).apply(StateTransforms.Data.ParseCif).commit(); // DEBUG
        AppModel.logCifOverview(cif.data!); // DEBUG
        // AppModel.logCifOverview(parsed); // DEBUG
        const volume: StateObjectSelector<PluginStateObject.Volume.Data> = parsed.volumes?.[0] ?? parsed.volume;
        const volumeData = volume.cell!.obj!.data;
        this.volume = volumeData;
        console.log('volume.grid:', volumeData.grid); // DEBUG

        this.volumeRepr = plugin.build()
            .to(volume)
            .apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volumeData, {
                type: 'isosurface',
                typeParams: { alpha: 1.0, isoValue: Volume.IsoValue.relative(-0.55) },
                color: 'uniform',
                colorParams: { value: Color(0x224899) }
            }));
        await this.volumeRepr.commit();

        this.currentSegments = [];
        // const segP = this.createSegment99999Plus(volumeData, 0);
        // const segM = this.createSegment99999Minus(volumeData, -0.55);
        // await this.showSegment(segP, [0.3, 0.7, 0.1]);
        // await this.showSegment(segM, [0.1, 0.3, 0.7]);

        UrlFragmentInfo.set({ example: 'xBioimage', entry: entryId });
        this.exampleType.next('xBioimage');
        console.timeEnd('Load example');
    }

    async loadExampleMeshes(entryId: string = 'empiar-10070', segments: 'fg' | 'all' = 'fg') {
        console.time('Load example');
        const source = AppModel.splitEntryId(entryId).source;
        let error = undefined;

        try {
            await this.plugin.clear();

            this.metadata = await API2.getMetadata(source, entryId);
            if (segments === 'fg') {
                const bgSegments = [13, 15];
                MetadataUtils.dropSegments(this.metadata, bgSegments);
            }

            this.meshSegmentNodes = {};
            this.showMeshSegments(this.metadata!.annotation.segment_list, entryId);
        } catch (ex) {
            this.metadata = undefined;
            error = ex;
            throw ex;
        } finally {
            UrlFragmentInfo.set({ example: 'xMeshes', entry: entryId });
            this.entryId.next(entryId);
            this.annotation.next(this.metadata?.annotation);
            this.exampleType.next('xMeshes');
            this.error.next(error);
            console.timeEnd('Load example');
        }
    }

    async loadExampleMeshStreaming(entryId: string = 'empiar-10070') {
        console.time('Load example');
        const source = AppModel.splitEntryId(entryId).source as 'empiar' | 'emdb';
        let error = undefined;

        try {
            await this.plugin.clear();
            this.metadata = await API2.getMetadata(source, entryId);
            MeshExamples.runMeshStreamingExample(this.plugin, source, entryId, API2.volumeServerUrl);
        } catch (ex) {
            this.metadata = undefined;
            error = ex;
            throw ex;
        } finally {
            UrlFragmentInfo.set({ example: 'xMeshStreaming', entry: entryId });
            this.entryId.next(entryId);
            this.annotation.next(this.metadata?.annotation);
            this.exampleType.next('xMeshStreaming');
            this.error.next(error);
            console.timeEnd('Load example');
        }
    }

    async loadExampleAuto(entryId: string = 'emd-1832') {
        console.time('Load example');
        this.status.next('loading');
        const source = AppModel.splitEntryId(entryId).source as 'empiar' | 'emdb';
        let error = undefined;
        let pdbs: string[] = [];

        try {
            await this.plugin.clear();
            this.plugin.behaviors.layout.leftPanelTabName.next('data');

            const metadataPromise = API2.getMetadata(source, entryId);
            const isoLevelPromise = AppModel.getIsovalue(entryId);
            const pdbsPromise = AppModel.getPdbIdsForEmdbEntry(entryId);
            this.metadata = await metadataPromise;


            const hasVolumes = this.metadata.grid.volumes.volume_downsamplings.length > 0;
            const hasLattices = this.metadata.grid.segmentation_lattices.segmentation_lattice_ids.length > 0;
            const hasMeshes = this.metadata.grid.segmentation_meshes.mesh_component_numbers.segment_ids !== undefined;

            // const A = 10 ** 4;
            // const BOX: [[number, number, number], [number, number, number]] = [[-A, -A, -A], [A, A, A]];
            const BOX = null;
            const MAX_VOXELS = 10 ** 7;

            // DEBUG
            // const debugVolumeInfo = false;
            // if (debugVolumeInfo) {
            //     const url = API2.volumeInfoUrl(source, entryId);
            //     const data = await this.plugin.builders.data.download({ url, isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
            //     const cif = await this.plugin.build().to(data).apply(StateTransforms.Data.ParseCif).commit();
            //     AppModel.logCifOverview(cif.data!, url); // TODO when could cif.data be undefined?
            // }

            // // DEBUG
            // const debugMeshesBcif = false;
            // const debugSegment = 1;
            // const debugDetail = 10;
            // if (debugMeshesBcif) {
            //     const url = API2.meshUrl_Bcif(source, entryId, debugSegment, debugDetail);
            //     const data = await this.plugin.builders.data.download({ url, isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
            //     const cif = await this.plugin.build().to(data).apply(StateTransforms.Data.ParseCif).commit();
            //     AppModel.logCifOverview(cif.data!, url); // TODO when could cif.data be undefined?
            // }

            if (hasVolumes) {
                // const isoLevel = { kind: 'relative', value: 2.73}; // rel 2.73 (abs 0.42) is OK for emd-1832
                const isoLevel = await isoLevelPromise;
                const url = API2.volumeUrl(source, entryId, BOX, MAX_VOXELS);
                const data = await this.plugin.builders.data.download({ url, isBinary: true, label: `Volume Data: ${url}` }, { state: { isGhost: USE_GHOST_NODES } });
                // const cif = await this.plugin.build().to(data).apply(StateTransforms.Data.ParseCif).commit(); AppModel.logCifOverview(cif.data!); // DEBUG
                const parsed = await this.plugin.dataFormats.get('dscif')!.parse(this.plugin, data, { entryId });
                const volume: StateObjectSelector<PluginStateObject.Volume.Data> = parsed.volumes?.[0] ?? parsed.volume;
                let volumeData = volume.cell!.obj!.data;
                this.volume = volumeData;
                await this.plugin.build()
                    .to(volume)
                    .apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volumeData, {
                        type: 'isosurface',
                        typeParams: { alpha: 0.2, isoValue: Volume.adjustedIsoValue(volumeData, isoLevel.value, isoLevel.kind) },
                        color: 'uniform',
                        colorParams: { value: Color(0x121212) }
                    }))
                    .commit();
            }
            if (hasLattices) {
                const url = API2.latticeUrl(source, entryId, 0, BOX, MAX_VOXELS);
                const data = await this.plugin.builders.data.download({ url, isBinary: true, label: `Segmentation Data: ${url}` }, { state: { isGhost: USE_GHOST_NODES } });
                const cif = await this.plugin.build().to(data).apply(StateTransforms.Data.ParseCif).commit();
                AppModel.logCifOverview(cif.data!, url); // TODO when could cif.data be undefined?
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

            pdbs = await pdbsPromise;
        } catch (ex) {
            this.metadata = undefined;
            error = ex;
            throw ex;
        } finally {
            UrlFragmentInfo.set({ example: 'xAuto', entry: entryId });
            this.entryId.next(entryId);
            this.annotation.next(this.metadata?.annotation);
            this.exampleType.next('xAuto');
            this.error.next(error);
            this.pdbs.next(pdbs);
            this.currentPdb.next(undefined);
            this.status.next(error ? 'error' : 'ready');
            console.timeEnd('Load example');
        }
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

    private static nodeExists(node: StateObjectSelector): boolean {
        try {
            return node.checkValid();
        } catch {
            return false;
        }
    }

    private getOrCreateGroup(parent: StateBuilder.To<any>, group?: StateObjectSelector, params?: { label?: string, description?: string }, options?: Partial<StateTransform.Options>) {
        if (group && AppModel.nodeExists(group)) {
            return group;
        } else {
            return parent.apply(CreateGroup, params, options).selector;
        }
    }

    async showPdb(pdbId: string | undefined) {
        this.status.next('loading');
        console.log('showPdb', pdbId, this.pdbModelNodes);
        try {
            const update = this.plugin.build();

            for (const pdb in this.pdbModelNodes) {
                const node = this.pdbModelNodes[pdb];
                if (!AppModel.nodeExists(node)) {
                    delete this.pdbModelNodes[pdb];
                    continue;
                }
                setSubtreeVisibility(node.state!, node.ref, true);  // hide
            }

            if (pdbId) {
                let pdbNode = this.pdbModelNodes[pdbId];
                if (!pdbNode) {
                    pdbNode = await this.loadPdb(pdbId);
                    this.pdbModelNodes[pdbId] = pdbNode;
                }
                setSubtreeVisibility(pdbNode.state!, pdbNode.ref, false);  // show
            }
            await update.commit();
            this.currentPdb.next(pdbId);
            this.status.next('ready');
        } catch (ex) {
            this.status.next('error');
            throw ex;
        }
    }

    /** Make visible the specified set of lattice segments */
    async showSegments(segments: Segment[]) {
        if (segments.length === 1) {
            this.currentSegment.next(segments[0]);
        } else {
            this.currentSegment.next(undefined);
        }

        const update = this.plugin.build();

        this.segmentationGroup = this.getOrCreateGroup(update.toRoot(), this.segmentationGroup, { label: 'Segmentation' });
        const group = this.segmentationGroup;

        for (const l of this.segmentationNodes) update.delete(l);
        this.segmentationNodes = [];

        console.log('StateTransforms.Representation.VolumeRepresentation3D', StateTransforms.Representation.VolumeRepresentation3D);
        for (const s of segments) {
            const volume = this.segmentation?.createSegment(s.id);
            Volume.PickingGranularity.set(volume!, 'volume');
            const root = update.to(group).apply(CreateVolume, { volume, label: `Segment ${s.id}`, description: s.biological_annotation?.name }, { state: { isCollapsed: true } });
            this.segmentationNodes.push(root.selector);

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

    /** Make visible the specified set of mesh segments */
    async showMeshSegments(segments: Segment[], entryId: string) {
        if (segments.length === 1) {
            this.currentSegment.next(segments[0]);
        } else {
            this.currentSegment.next(undefined);
        }

        for (const segid in this.meshSegmentNodes) {
            const node = this.meshSegmentNodes[segid];
            if (!AppModel.nodeExists(node)) {
                delete this.meshSegmentNodes[segid];
                continue;
            }
            setSubtreeVisibility(node.state!, node.ref, true);  // hide
        }
        for (const seg of segments) {
            let node = this.meshSegmentNodes[seg.id];
            if (!node) {
                const detail = MetadataUtils.getSufficientDetail(this.metadata!, seg.id, DEFAULT_DETAIL);
                const color = seg.colour.length >= 3 ? Color.fromNormalizedArray(seg.colour, 0) : ColorNames.gray;
                node = await MeshExamples.createMeshFromUrl(this.plugin, API2.meshUrl_Bcif(AppModel.splitEntryId(entryId).source, entryId, seg.id, detail), seg.id, detail, true, false, color);
                this.meshSegmentNodes[seg.id] = node;
            }
            setSubtreeVisibility(node.state!, node.ref, false);  // show
        }
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

    /** Split entry ID (e.g. 'emd-1832') into source ('emdb') and number ('1832') */
    static splitEntryId(entryId: string) {
        const PREFIX_TO_SOURCE: { [prefix: string]: string } = { 'empiar': 'empiar', 'emd': 'emdb' };
        const [prefix, entry] = entryId.split('-');
        return {
            source: PREFIX_TO_SOURCE[prefix],
            entryNumber: entry
        };
    }

    /** Create entry ID (e.g. 'emd-1832') for a combination of source ('emdb') and number ('1832') */
    static createEntryId(source: string, entryNumber: string | number) {
        const SOURCE_TO_PREFIX: { [prefix: string]: string } = { 'empiar': 'empiar', 'emdb': 'emd' };
        return `${SOURCE_TO_PREFIX[source]}-${entryNumber}`;
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
        this.segmentationNodes.push(root.selector);

        const seg = root.apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volume, {
            type: 'isosurface',
            typeParams: { alpha: opacity, isoValue: Volume.IsoValue.absolute(0.95), transparentBackfaces: 'off', doubleSided: false, flatShaded: true },
            color: 'uniform',
            colorParams: { value: Color.fromNormalizedArray(color, 0) }
        }));

        this.currentSegments.push(seg.selector);

        await update.commit();
    }



    private logStuff(plugin: PluginUIContext, repr: StateBuilder.Root): void {
        console.log('plugin:\n', plugin);
        console.log('repr:\n', repr);
        console.log('tree:\n', repr.currentTree);
        console.log('children:', repr.currentTree.children.size);
    }

    private static logCifOverview(cifData: CifFile, url: string = ''): void {
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

    /** Try to get author-defined contour value for isosurface from EMDB API. Return relative value 1.0, if not applicable or fails.  */
    private static async getIsovalue(entryId: string): Promise<{ kind: 'absolute' | 'relative', value: number }> {
        const split = AppModel.splitEntryId(entryId);
        if (split.source === 'emdb') {
            try {
                const response = await fetch(`https://www.ebi.ac.uk/emdb/api/entry/map/${split.entryNumber}`);
                const json = await response.json();
                const contours: any[] = json?.map?.contour_list?.contour;
                if (contours && contours.length > 0) {
                    const theContour = contours.find(c => c.primary) || contours[0];
                    return { kind: 'absolute', value: theContour.level };
                }
            } catch {
                // do nothing
            }
        }
        return { kind: 'relative', value: 1.0 };
    }

    private static async getPdbIdsForEmdbEntry(entryId: string): Promise<string[]> {
        const split = AppModel.splitEntryId(entryId);
        const result = [];
        if (split.source === 'emdb') {
            entryId = entryId.toUpperCase();
            const apiUrl = `https://www.ebi.ac.uk/pdbe/api/emdb/entry/fitted/${entryId}`;
            try {
                const response = await fetch(apiUrl);
                if (response.ok) {
                    const json = await response.json();
                    const jsonEntry = json[entryId] ?? [];
                    for (const record of jsonEntry) {
                        const pdbs = record?.fitted_emdb_id_list?.pdb_id ?? [];
                        result.push(...pdbs);
                    }
                }
            } catch (ex) {
                // do nothing
            }
        }
        return result;
    }
}

