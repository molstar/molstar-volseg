/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */

import { PluginStateObject } from 'molstar/lib/mol-plugin-state/objects';
import { PluginContext } from 'molstar/lib/mol-plugin/context';
import { StateObjectRef } from 'molstar/lib/mol-state';
import { GEOMETRIC_SEGMENTATION_NODE_TAG, MESH_SEGMENTATION_NODE_TAG, LATTICE_SEGMENTATION_NODE_TAG, VOLUME_NODE_TAG } from '../volumes-and-segmentations/entry-root';
import { ProjectGeometricSegmentationData, ProjectGeometricSegmentationDataParamsValues, ProjectLatticeSegmentationDataParamsValues, ProjectMeshData, ProjectMeshSegmentationDataParamsValues, ProjectSegmentationData, ProjectVolumeData, VolsegEntryFromFile, VolsegGlobalStateFromFile, VolsegStateFromEntry } from '../volumes-and-segmentations/transformers';
import { getSegmentLabelsFromDescriptions } from '../volumes-and-segmentations/volseg-api/utils';

export async function loadCVSXFromAnything(plugin: PluginContext, data: StateObjectRef<PluginStateObject.Data.Binary | PluginStateObject.Data.String>) {
    await plugin.build().to(data).apply(VolsegGlobalStateFromFile, {}, { state: { isGhost: true } }).commit();

    const entryNode = await plugin.build().to(data).apply(VolsegEntryFromFile).commit();
    await plugin.build().to(entryNode).apply(VolsegStateFromEntry, {}, { state: { isGhost: true } }).commit();


    if (entryNode.data) {
        // TODO: change - get from filesIndex, but from metadata is ok too
        // since query contains a single timeframe, or all
        const entryData = entryNode.data;
        let timeframeIndex = entryData.metadata!.value!.raw.grid.volumes.time_info.start;
        let channelIds = entryData.metadata!.value!.raw.grid.volumes.channel_ids;
        if (entryData.filesData!.query.channel_id) {
            channelIds = [entryData.filesData!.query.channel_id];
        }
        if (entryData.filesData!.query.time) {
            timeframeIndex = entryData.filesData!.query.time;
        }
        // always has Volumes
        const group = await entryNode.data.volumeData.createVolumeGroup();
        const updatedChannelsData = [];
        const results = [];
        for (const channelId of channelIds) {
            const volumeParams = { timeframeIndex: timeframeIndex, channelId: channelId };
            const volumeNode = await plugin.build().to(group).apply(ProjectVolumeData, volumeParams, { tags: [VOLUME_NODE_TAG] }).commit();
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
        const hasLattices = entryData.filesData?.latticeSegmentations;
        if (hasLattices) {
            // filter only lattices for timeframeIndex
            const latticesForTimeframeIndex = hasLattices.filter(l => l.timeframeIndex === timeframeIndex);
            const segmentationIds = latticesForTimeframeIndex.map(l => l.segmentationId);

            // loop over lattices and create one for each
            const group = await entryNode.data.latticeSegmentationData.createSegmentationGroup();
            for (const segmentationId of segmentationIds) {
                const descriptionsForLattice = entryNode.data.metadata.value!.getDescriptions(
                    segmentationId,
                    'lattice',
                    timeframeIndex
                );
                const segmentLabels = getSegmentLabelsFromDescriptions(descriptionsForLattice);
                const segmentationParams: ProjectLatticeSegmentationDataParamsValues = {
                    timeframeIndex: timeframeIndex,
                    segmentationId: segmentationId,
                    segmentLabels: segmentLabels as any,
                    ownerId: entryNode.data.ref
                };
                const segmentationNode = await plugin.build().to(group).apply(ProjectSegmentationData, segmentationParams, { tags: [LATTICE_SEGMENTATION_NODE_TAG] }).commit();
                await entryNode.data.latticeSegmentationData.createSegmentationRepresentation3D(segmentationNode, segmentationParams);
            }

        }

        const hasGeometricSegmentation = entryData.filesData?.geometricSegmentations;
        if (hasGeometricSegmentation) {
            const segmentationIds = hasGeometricSegmentation.map(g => g.segmentationId);
            const group = await entryNode.data.geometricSegmentationData.createGeometricSegmentationGroup();
            for (const segmentationId of segmentationIds) {
                const geometricSegmentationParams: ProjectGeometricSegmentationDataParamsValues = {
                    segmentationId: segmentationId,
                    timeframeIndex: timeframeIndex
                };
                const geometricSegmentationNode = await plugin.build().to(group).apply(ProjectGeometricSegmentationData, geometricSegmentationParams, { tags: [GEOMETRIC_SEGMENTATION_NODE_TAG] }).commit();
                await entryNode.data.geometricSegmentationData.createGeometricSegmentationRepresentation3D(geometricSegmentationNode, geometricSegmentationParams);
            }
        }

        const hasMeshes = entryData.filesData?.meshSegmentations;
        if (hasMeshes) {
            const segmentationIds = hasMeshes.map(m => m.segmentationId);
            const group = await entryNode.data.meshSegmentationData.createMeshGroup();
            for (const segmentationId of segmentationIds) {
                const meshSegmentParams = entryData.meshSegmentationData.getMeshSegmentParams(segmentationId, timeframeIndex);
                const meshParams: ProjectMeshSegmentationDataParamsValues = {
                    meshSegmentParams: meshSegmentParams,
                    segmentationId: segmentationId,
                    timeframeIndex: timeframeIndex
                };
                const meshNode = await plugin.build().to(group).apply(ProjectMeshData, meshParams, { tags: [MESH_SEGMENTATION_NODE_TAG] }).commit();
                await entryNode.data.meshSegmentationData.createMeshRepresentation3D(meshNode, meshParams);
            }
        }


    };
    return entryNode;
}