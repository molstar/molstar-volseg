/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Adam Midlik <midlik@gmail.com>
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */

import { PluginStateObject as SO } from 'molstar/lib/mol-plugin-state/objects'
import { PluginBehavior } from 'molstar/lib/mol-plugin/behavior';
import { PluginConfigItem } from 'molstar/lib/mol-plugin/config';
import { PluginContext } from 'molstar/lib/mol-plugin/context';
import { StateAction } from 'molstar/lib/mol-state';
import { Task } from 'molstar/lib/mol-task';
import { DEFAULT_VOLSEG_SERVER, VolumeApiV2 } from './volseg-api/api';
import { GEOMETRIC_SEGMENTATION_NODE_TAG, MESH_SEGMENTATION_NODE_TAG, LATTICE_SEGMENTATION_NODE_TAG, VOLUME_NODE_TAG, VolsegEntryData, VolsegEntryParamValues, createLoadVolsegParams, VolsegEntry, LoadVolsegParamValues } from './entry-root';
import { VolsegGlobalState } from './global-state';
import { createEntryId, isDefined } from './helpers';
import { ProjectGeometricSegmentationData, ProjectGeometricSegmentationDataParamsValues, ProjectMeshData, ProjectMeshSegmentationDataParamsValues, ProjectSegmentationData, ProjectLatticeSegmentationDataParamsValues, ProjectVolumeData, VolsegEntryFromRoot, VolsegGlobalStateFromRoot, VolsegStateFromEntry } from './transformers';
import { VolsegUI } from './ui';
import { createSegmentKey, getSegmentLabelsFromDescriptions } from './volseg-api/utils';
import { Source, actionShowSegments, findNodesByRef } from '../../common';

// const DEBUGGING = typeof window !== 'undefined' ? window?.location?.hostname === 'localhost' || '127.0.0.1' : false;
const DEBUGGING = typeof window !== 'undefined' ? window?.location?.hostname === 'localhost' : false;

export const VolsegVolumeServerConfig = {
    // DefaultServer: new PluginConfigItem('volseg-volume-server', DEFAULT_VOLUME_SERVER_V2),
    DefaultServer: new PluginConfigItem('volseg-volume-server', DEBUGGING ? 'http://localhost:9000/v1' : DEFAULT_VOLSEG_SERVER),
};


export const Volseg = PluginBehavior.create<{ autoAttach: boolean, showTooltip: boolean }>({
    name: 'volseg-v2',
    category: 'misc',
    display: {
        name: 'Volseg',
        description: 'Volseg'
    },
    ctor: class extends PluginBehavior.Handler<{ autoAttach: boolean, showTooltip: boolean }> {
        register() {
            this.ctx.state.data.actions.add(LoadVolseg);
            this.ctx.customStructureControls.set('volseg-v2', VolsegUI as any);
            this.initializeEntryLists(); // do not await

            const entries = new Map<string, VolsegEntryData>();
            this.subscribeObservable(this.ctx.state.data.events.cell.created, o => {
                if (o.cell.obj instanceof VolsegEntryData) entries.set(o.ref, o.cell.obj);
            });

            this.subscribeObservable(this.ctx.state.data.events.cell.removed, o => {
                if (entries.has(o.ref)) {
                    entries.get(o.ref)!.dispose();
                    entries.delete(o.ref);
                }
            });
        }
        unregister() {
            this.ctx.state.data.actions.remove(LoadVolseg);
            this.ctx.customStructureControls.delete('volseg-v2');
        }
        private async initializeEntryLists() {
            const apiUrl = this.ctx.config.get(VolsegVolumeServerConfig.DefaultServer) ?? DEFAULT_VOLSEG_SERVER;
            const api = new VolumeApiV2(apiUrl);
            const entryLists = await api.getEntryList(10 ** 6);
            Object.values(entryLists).forEach(l => l.sort());
            (this.ctx.customState as any).volsegAvailableEntries = entryLists;
        }
    }
});


export async function findOrCreateVolsegEntry(entryId: string, source: string, plugin: PluginContext) {
    const nodes = plugin.state.data.selectQ(q => q.ofType(VolsegEntry)).map(cell => cell?.obj).filter(isDefined);
    const targetNode = nodes.find(n => n.data.entryId === entryId && n.data.source === source);
    debugger;
    if (targetNode) {
        // TODO: return selector?
        // return targetNode;
        const n = findNodesByRef(plugin, targetNode.data.ref);
        const nn = findNodesByRef(plugin, n.transform.ref);
        console.log(nn);
        debugger;
        return nn;
    }
    else {
        const entryParams = {
            serverUrl: plugin?.config.get(VolsegVolumeServerConfig.DefaultServer) ?? DEFAULT_VOLSEG_SERVER,
            source: source as Source,
            entryId: entryId
        };
        // const entryParams: LoadVolsegParamValues = {
        //     serverUrl: defaultVolumeServer,
        //     source: SourceChoice.PDSelect(),
        //     entryId: ParamDefinition.Text('emd-1832', { description: 'Entry identifier, including the source prefix, e.g. "emd-1832"' }),
        // };
        debugger;
        const entryNode = await plugin.state.data.build().toRoot().apply(VolsegEntryFromRoot, entryParams).commit();
        return entryNode;
    }
}

export const LoadVolseg = StateAction.build({
    display: { name: 'Load Volume & Segmentation' },
    from: SO.Root,
    params: (a, plugin: PluginContext) => {
        const res = createLoadVolsegParams(plugin, (plugin.customState as any).volsegAvailableEntries);
        return res;
    },
})(({ params, state }, ctx: PluginContext) => Task.create('Loading Volume & Segmentation', taskCtx => {
    return state.transaction(async () => {
        const entryParams = VolsegEntryParamValues.fromLoadVolsegParamValues(params);
        if (entryParams.entryId.trim().length === 0) {
            alert('Must specify Entry Id!');
            throw new Error('Specify Entry Id');
        }
        if (!entryParams.entryId.includes('-')) {
            // add source prefix if the user omitted it (e.g. 1832 -> emd-1832)
            entryParams.entryId = createEntryId(entryParams.source, entryParams.entryId);
        }
        ctx.behaviors.layout.leftPanelTabName.next('data');

        const globalStateNode = ctx.state.data.selectQ(q => q.ofType(VolsegGlobalState))[0];
        if (!globalStateNode) {
            await state.build().toRoot().apply(VolsegGlobalStateFromRoot, {}, { state: { isGhost: !DEBUGGING } }).commit();
        }
        const entryNode = await state.build().toRoot().apply(VolsegEntryFromRoot, entryParams).commit();
        await state.build().to(entryNode).apply(VolsegStateFromEntry, {}, { state: { isGhost: !DEBUGGING } }).commit();
        if (entryNode.data) {
            const entryData = entryNode.data;
            const hasVolumes = entryNode.data.metadata.value!.raw.grid.volumes.volume_sampling_info.spatial_downsampling_levels.length > 0;
            if (hasVolumes) {
                const group = await entryNode.data.volumeData.createVolumeGroup();
                const updatedChannelsData: any = [];
                const results: any = [];
                const channelIds = entryNode.data.metadata.value!.raw.grid.volumes.channel_ids;
                for (const channelId of channelIds) {
                    const volumeParams = { timeframeIndex: 0, channelId: channelId };
                    const volumeNode = await state.build().to(group).apply(ProjectVolumeData, volumeParams, { tags: [VOLUME_NODE_TAG] }).commit();
                    const result = await entryNode.data.volumeData.createVolumeRepresentation3D(volumeNode, volumeParams);
                    results.push(result);
                }
                for (const result of results) {
                    if (result) {
                        const isovalue = result.isovalue.kind === 'relative' ? result.isovalue.relativeValue : result.isovalue.absoluteValue;
                        updatedChannelsData.push(
                            {
                                channelId: result.channelId, volumeIsovalueKind: result.isovalue.kind, volumeIsovalueValue: isovalue, volumeType: result.volumeType, volumeOpacity: result.opacity,
                                label: result.label,
                                color: result.color
                            }
                        );
                    }
                }
                await entryNode.data.updateStateNode({ channelsData: [...updatedChannelsData] });
            }

            const hasLattices = entryNode.data.metadata.value!.raw.grid.segmentation_lattices;
            if (hasLattices && hasLattices.segmentation_ids.length > 0) {
                const group = await entryNode.data.latticeSegmentationData.createSegmentationGroup();
                const segmentationIds = hasLattices.segmentation_ids;
                for (const segmentationId of segmentationIds) {
                    const descriptionsForLattice = entryNode.data.metadata.value!.getDescriptions(
                        segmentationId,
                        'lattice',
                        0
                    );
                    const segmentLabels = getSegmentLabelsFromDescriptions(descriptionsForLattice);
                    const segmentationParams: ProjectLatticeSegmentationDataParamsValues = {
                        timeframeIndex: 0,
                        segmentationId: segmentationId,
                        segmentLabels: segmentLabels,
                        ownerId: entryNode.data.ref
                    };
                    const segmentationNode = await state.build().to(group).apply(ProjectSegmentationData, segmentationParams, { tags: [LATTICE_SEGMENTATION_NODE_TAG] }).commit();
                    await entryNode.data.latticeSegmentationData.createSegmentationRepresentation3D(segmentationNode, segmentationParams);
                }
            };

            const hasMeshes = entryNode.data.metadata.value!.raw.grid.segmentation_meshes;
            if (hasMeshes && hasMeshes.segmentation_ids.length > 0) {
                const group = await entryNode.data.meshSegmentationData.createMeshGroup();
                const segmentationIds = hasMeshes.segmentation_ids;
                for (const segmentationId of segmentationIds) {
                    const timeframeIndex = 0;
                    const meshSegmentParams = entryData.meshSegmentationData.getMeshSegmentParams(segmentationId, timeframeIndex);
                    const meshParams: ProjectMeshSegmentationDataParamsValues = {
                        meshSegmentParams: meshSegmentParams,
                        segmentationId: segmentationId,
                        timeframeIndex: timeframeIndex
                    };
                    const meshNode = await state.build().to(group).apply(ProjectMeshData, meshParams, { tags: [MESH_SEGMENTATION_NODE_TAG] }).commit();
                    await entryNode.data.meshSegmentationData.createMeshRepresentation3D(meshNode, meshParams);
                }


            }
            const hasGeometricSegmentation = entryData.metadata.value!.raw.grid.geometric_segmentation;
            if (hasGeometricSegmentation && hasGeometricSegmentation.segmentation_ids.length > 0) {
                const group = await entryNode.data.geometricSegmentationData.createGeometricSegmentationGroup();
                // const timeInfo = this.entryData.metadata.value!.raw.grid.geometric_segmentation!.time_info;
                for (const segmentationId of hasGeometricSegmentation.segmentation_ids) {
                    const timeframeIndex = 0;
                    const geometricSegmentationParams: ProjectGeometricSegmentationDataParamsValues = {
                        segmentationId: segmentationId,
                        timeframeIndex: timeframeIndex
                    };
                    const geometricSegmentationNode = await state.build().to(group).apply(ProjectGeometricSegmentationData, geometricSegmentationParams, { tags: [GEOMETRIC_SEGMENTATION_NODE_TAG] }).commit();
                    await entryNode.data.geometricSegmentationData.createGeometricSegmentationRepresentation3D(geometricSegmentationNode, geometricSegmentationParams);
                }
            }
            const allAnnotationsForTimeframe = entryData.metadata.value!.getAllAnnotations(0);
            const allSegmentKeysForTimeframe = allAnnotationsForTimeframe.map(a => {
                return createSegmentKey(a.segment_id, a.segmentation_id, a.segment_kind);
            }
            );
            await actionShowSegments(allSegmentKeysForTimeframe, entryData);
        }
    }).runInContext(taskCtx);
}));