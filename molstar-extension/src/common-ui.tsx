/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */

import { Button, ExpandGroup, IconButton, TextInput } from 'molstar/lib/mol-plugin-ui/controls/common';
import { sleep } from 'molstar/lib/mol-util/sleep';
import { actionSelectSegment, actionToggleAllFilteredSegments, actionToggleSegment } from './common';
import { WaitingButton } from './extensions/volumes-and-segmentations/ui';
import { createSegmentKey, parseSegmentKey } from './extensions/volumes-and-segmentations/volseg-api/utils';
import * as Icons from 'molstar/lib/mol-plugin-ui/controls/icons';
import { useBehavior } from 'molstar/lib/mol-plugin-ui/hooks/use-behavior';
import { VolsegEntryData } from './extensions/volumes-and-segmentations/entry-root';
import Markdown from 'react-markdown';
import { capitalize } from 'molstar/lib/mol-util/string';
import { useState } from 'react';
import { DescriptionData, DetailsText, ExternalReference } from './extensions/volumes-and-segmentations/volseg-api/data';

export function DescriptionTextUI({ descriptionText: d }: { descriptionText: DetailsText }) {
    if (d.format === 'markdown') {
        return <>
            <br />
            <br />
            <b>Description: </b>
            <Markdown skipHtml>{d.text}</Markdown>
        </>;
    } else if (d.format === 'text') {
        return <>
            <br />
            <br />
            <b>Description: </b>
            <p>{d.text}</p>
        </>;
    }
}

// Renders all external references
export function ExternalReferencesUI({ externalReferences: e }: { externalReferences: ExternalReference[] }) {
    return <>
        {e.map(ref => {
            return <p key={ref.id} style={{ marginTop: 4 }}>
                {ref.url ? <a href={ref.url}>{ref.resource}:{ref.accession}</a> :
                    <small>{ref.resource}:{ref.accession}</small>}
                <br />
                <b>{capitalize(ref.label ? ref.label : '')}</b><br />
                {ref.description}
            </p>;
        }
        )}
    </>;
}

export function EntryDescriptionUI({ entryDescriptionData: e }: { entryDescriptionData: DescriptionData }) {
    return <ExpandGroup header='Entry description data'>
        <div key={e.id}>
            {e.name ?? ''}
            {e.details && <DescriptionTextUI descriptionText={e.details}></DescriptionTextUI>}
            {e.external_references && <ExternalReferencesUI externalReferences={e.external_references} />}
        </div>
    </ExpandGroup>;
}

export const MetadataTextFilter = ({ setFilteredDescriptions, descriptions, model }: { setFilteredDescriptions: any, descriptions: DescriptionData[], model: VolsegEntryData }) => {
    const [text, setText] = useState('');

    function filterDescriptions(keyword: string) {
        return model.metadata!.value!.filterDescriptions(descriptions, keyword);
    }

    return (
        <TextInput
            style={{ order: 1, flex: '1 1 auto', minWidth: 0, marginBlock: 1 }} className='msp-form-control'
            value={text}
            placeholder="Type keyword to filter segments..."
            onChange={newText => {
                setText(newText);
                const filteredDescriptions = filterDescriptions(newText);

                setFilteredDescriptions(filteredDescriptions);
            }}
        />
    );
};

export function DescriptionsListItem({ model, d, currentTimeframe, selectedSegmentDescription, visibleSegmentKeys }: { model: VolsegEntryData, d: DescriptionData, currentTimeframe: number, selectedSegmentDescription: DescriptionData | undefined, visibleSegmentKeys: string[] }) {
    const metadata = useBehavior(model.metadata);
    if (d.target_kind === 'entry' || !d.target_id || d.is_hidden === true) return;
    // NOTE: if time is a single number
    if (d.time && Number.isFinite(d.time) && d.time !== currentTimeframe) return;
    // NOTE: if time is array
    if (d.time && Array.isArray(d.time) && d.time.every(i => Number.isFinite(i)) && !(d.time as number[]).includes(currentTimeframe)) return;
    const segmentKey = createSegmentKey(d.target_id.segment_id, d.target_id.segmentation_id, d.target_kind);

    const targetDescriptionCurrent = metadata!.raw.annotation!.descriptions[d.id];
    d = targetDescriptionCurrent;
    if (d.target_kind === 'entry' || !d.target_id || d.is_hidden === true) return;

    return <div className='msp-flex-row' style={{ marginTop: '1px' }} key={`${d.target_id?.segment_id}:${d.target_id?.segmentation_id}:${d.target_kind}`}
    >

        <Button noOverflow flex onClick={() => actionSelectSegment(model, d !== selectedSegmentDescription ? segmentKey : undefined)}
            style={{
                fontWeight: d.target_id.segment_id === selectedSegmentDescription?.target_id?.segment_id
                    && d.target_id.segmentation_id === selectedSegmentDescription?.target_id.segmentation_id
                    ? 'bold' : undefined, textAlign: 'left'
            }}>
            <div title={d.name ?? 'Unnamed segment'} style={{ maxWidth: 240, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {d.name ?? 'Unnamed segment'} ({d.target_id?.segment_id}) ({d.target_id?.segmentation_id})
            </div>
        </Button>
        <IconButton svg={visibleSegmentKeys.includes(segmentKey) ? Icons.VisibilityOutlinedSvg : Icons.VisibilityOffOutlinedSvg}
            title={visibleSegmentKeys.includes(segmentKey) ? 'Hide segment' : 'Show segment'}
            onClick={() => actionToggleSegment(model, segmentKey)} />
    </div>;
}

export function DescriptionsList({ model, targetSegmentationId, targetKind }: { model: VolsegEntryData, targetSegmentationId: string, targetKind: 'lattice' | 'mesh' | 'primitive' }) {
    const state = useBehavior(model.currentState);
    const currentTimeframe = useBehavior(model.currentTimeframe);
    const metadata = useBehavior(model.metadata);
    const allDescriptionsForSegmentationId = metadata!.getDescriptions(
        targetSegmentationId,
        targetKind,
        currentTimeframe
    );
    const [filteredDescriptions, setFilteredDescriptions] = useState(allDescriptionsForSegmentationId);
    const parsedSelectedSegmentKey = parseSegmentKey(state.selectedSegment);
    const { segmentId, segmentationId, kind } = parsedSelectedSegmentKey;
    const selectedSegmentDescriptions = model.metadata.value!.getSegmentDescription(segmentId, segmentationId, kind);
    // NOTE: for now single description
    const selectedSegmentDescription = selectedSegmentDescriptions ? selectedSegmentDescriptions[0] : undefined;
    const visibleSegmentKeys = state.visibleSegments.map(seg => seg.segmentKey);

    return <>
        <MetadataTextFilter setFilteredDescriptions={setFilteredDescriptions} descriptions={allDescriptionsForSegmentationId} model={model}></MetadataTextFilter>
        {filteredDescriptions.length > 0 && <div key={targetSegmentationId}>
            <WaitingButton onClick={async () => { await sleep(20); await actionToggleAllFilteredSegments(model, targetSegmentationId, targetKind, filteredDescriptions); }} style={{ marginTop: 1 }}>
                Toggle All segments
            </WaitingButton>
            <div style={{ maxHeight: 200, overflow: 'hidden', overflowY: 'auto', marginBlock: 1 }}>
                {filteredDescriptions.map(d => {
                    return <DescriptionsListItem key={d.id} model={model} d={d} currentTimeframe={currentTimeframe} selectedSegmentDescription={selectedSegmentDescription} visibleSegmentKeys={visibleSegmentKeys} />;
                }
                )}
            </div>
        </div>}</>;
}

export function SelectedSegmentDescription({ model, targetSegmentationId, targetKind }: { model: VolsegEntryData, targetSegmentationId: string, targetKind: 'lattice' | 'mesh' | 'primitive' }) {
    const state = useBehavior(model.currentState);
    useBehavior(model.currentTimeframe);
    const metadata = useBehavior(model.metadata);
    const anyDescriptions = metadata!.allDescriptions.length > 0;
    const parsedSelectedSegmentKey = parseSegmentKey(state.selectedSegment);
    const { segmentId, segmentationId, kind } = parsedSelectedSegmentKey;
    const selectedSegmentDescriptions = model.metadata.value!.getSegmentDescription(segmentId, segmentationId, kind);
    // NOTE: for now single description
    const selectedSegmentDescription = selectedSegmentDescriptions ? selectedSegmentDescriptions[0] : undefined;
    return <>{
        anyDescriptions && <ExpandGroup header='Selected segment descriptions' initiallyExpanded>
            <div style={{ paddingTop: 4, paddingRight: 8, maxHeight: 300, overflow: 'hidden', overflowY: 'auto' }}>
                {!selectedSegmentDescription && 'No segment selected'}
                {selectedSegmentDescription &&
                    selectedSegmentDescription.target_kind !== 'entry' &&
                    selectedSegmentDescription.target_id &&
                    <b>Segment {selectedSegmentDescription.target_id.segment_id} from segmentation {selectedSegmentDescription.target_id.segmentation_id}:<br />{selectedSegmentDescription.name ?? 'Unnamed segment'}</b>}
                {selectedSegmentDescription && selectedSegmentDescription.details &&
                    <DescriptionTextUI descriptionText={selectedSegmentDescription.details}></DescriptionTextUI>}
                {selectedSegmentDescription?.external_references &&
                    <ExternalReferencesUI externalReferences={selectedSegmentDescription.external_references}></ExternalReferencesUI>}
            </div>
        </ExpandGroup>
    }</>;

}