/**
 * Copyright (c) 2018-2024 mol* contributors, licensed under MIT, See LICENSE file for more info.
 *
 * @author Adam Midlik <midlik@gmail.com>
 * @author Aliaksei Chareshneu <chareshneu.tech@gmail.com>
 */
import Popup from 'reactjs-popup';
import 'reactjs-popup/dist/index.css';
import { useCallback, useEffect, useRef, useState } from 'react';
// import { ParamDefinition as PD } from 'molstar/lib/mol-util/param-definition';

import { CollapsableControls, CollapsableState } from 'molstar/lib/mol-plugin-ui/base';
import { Button, ControlRow, ExpandGroup } from 'molstar/lib/mol-plugin-ui/controls/common';
import * as Icons from 'molstar/lib/mol-plugin-ui/controls/icons';
import { ParameterControls } from 'molstar/lib/mol-plugin-ui/controls/parameters';
import { Slider } from 'molstar/lib/mol-plugin-ui/controls/slider';
import { useBehavior } from 'molstar/lib/mol-plugin-ui/hooks/use-behavior';
import { UpdateTransformControl } from 'molstar/lib/mol-plugin-ui/state/update-transform';
import { PluginContext } from 'molstar/lib/mol-plugin/context';
import { shallowEqualArrays } from 'molstar/lib/mol-util';
import { ParamDefinition as PD } from 'molstar/lib/mol-util/param-definition';
import { sleep } from 'molstar/lib/mol-util/sleep';

import { VolsegEntry, VolsegEntryData } from './entry-root';
import { SimpleVolumeParams, SimpleVolumeParamValues } from './entry-volume';
import { VolsegGlobalState, VolsegGlobalStateData, VolsegGlobalStateParams } from './global-state';
import { isDefined } from './helpers';
import { ProjectDataParamsValues, ProjectGeometricSegmentationDataParamsValues, ProjectLatticeSegmentationDataParamsValues, ProjectMeshSegmentationDataParamsValues } from './transformers';
import { State, StateObjectCell } from 'molstar/lib/mol-state';
import { PluginStateObject } from 'molstar/lib/mol-plugin-state/objects';
import { parseSegmentKey } from './volseg-api/utils';
import React from 'react';
import { VolsegGeometricSegmentation } from './shape_primitives';
import { VolsegMeshSegmentation } from '../meshes/mesh-extension';
import { findNodesByRef } from '../../common';
import { DescriptionsList, EntryDescriptionUI, SelectedSegmentDescription } from '../../common-ui';
import { JSONEditorComponent } from './jsoneditor-component';
import { combineLatest } from 'rxjs';

interface VolsegUIData {
    globalState?: VolsegGlobalStateData,
    availableNodes: VolsegEntry[],
    activeNode?: VolsegEntry,
}
namespace VolsegUIData {
    export function changeAvailableNodes(data: VolsegUIData, newNodes: VolsegEntry[]): VolsegUIData {
        const newActiveNode = newNodes.length > data.availableNodes.length ?
            newNodes[newNodes.length - 1]
            : newNodes.find(node => node.data.ref === data.activeNode?.data.ref) ?? newNodes[0];
        return { ...data, availableNodes: newNodes, activeNode: newActiveNode };
    }
    export function changeActiveNode(data: VolsegUIData, newActiveRef: string): VolsegUIData {
        const newActiveNode = data.availableNodes.find(node => node.data.ref === newActiveRef) ?? data.availableNodes[0];
        return { ...data, availableNodes: data.availableNodes, activeNode: newActiveNode };
    }
    export function equals(data1: VolsegUIData, data2: VolsegUIData) {
        return shallowEqualArrays(data1.availableNodes, data2.availableNodes) && data1.activeNode === data2.activeNode && data1.globalState === data2.globalState;
    }
}

export class VolsegUI extends CollapsableControls<{}, { data: VolsegUIData }> {
    protected defaultState(): CollapsableState & { data: VolsegUIData } {
        return {
            header: 'Volume & Segmentation',
            isCollapsed: true,
            brand: { accent: 'orange', svg: Icons.ExtensionSvg },
            data: {
                globalState: undefined,
                availableNodes: [],
                activeNode: undefined,
            }
        };
    }
    protected renderControls(): JSX.Element | null {
        return <VolsegControls plugin={this.plugin} data={this.state.data} setData={d => this.setState({ data: d })} />;
    }

    private syncState(state: State): void {
        const nodes = state.selectQ(q => q.ofType(VolsegEntry)).map(cell => cell?.obj).filter(isDefined);
        const isHidden = nodes.length === 0;
        const newData = VolsegUIData.changeAvailableNodes(this.state.data, nodes);
        if (!this.state.data.globalState?.isRegistered()) {
            const globalState = state.selectQ(q => q.ofType(VolsegGlobalState))[0]?.obj?.data;
            if (globalState) newData.globalState = globalState;
        }
        if (!VolsegUIData.equals(this.state.data, newData) || this.state.isHidden !== isHidden) {
            this.setState({ data: newData, isHidden: isHidden });
        }
    }

    componentDidMount(): void {
        this.setState({ isHidden: true, isCollapsed: false });
        this.syncState(this.plugin.state.data);
        this.subscribe(
            combineLatest([
                this.plugin.state.data.events.changed,
                this.plugin.behaviors.state.isAnimating,
            ]),
            ([e, isAnimating]) => {
                if (isAnimating) return;

                this.syncState(e.state);
            },
        );
    }
}

function VolsegControls({ plugin, data, setData }: { plugin: PluginContext, data: VolsegUIData, setData: (d: VolsegUIData) => void }) {
    const entryData = data.activeNode?.data;
    if (!entryData) {
        return <p>No data!</p>;
    }
    if (!data.globalState) {
        return <p>No global state!</p>;
    }

    const params = {
        /** Reference to the active VolsegEntry node */
        entry: PD.Select(data.activeNode!.data.ref, data.availableNodes.map(entry => [entry.data.ref, entry.data.entryId]))
    };
    const values: PD.Values<typeof params> = {
        entry: data.activeNode!.data.ref,
    };

    const globalState = useBehavior(data.globalState.currentState);

    return <>
        <ParameterControls params={params} values={values} onChangeValues={next => setData(VolsegUIData.changeActiveNode(data, next.entry))} />

        <TimeFrameSlider entryData={entryData} />
        <ExpandGroup header='Global options'>
            <WaitingParameterControls params={VolsegGlobalStateParams} values={globalState} onChangeValues={async next => await data.globalState?.updateState(plugin, next)} />
        </ExpandGroup>

        <VolsegEntryControls entryData={entryData} key={entryData.ref} />
    </>;
}

function VolsegEntryControls({ entryData }: { entryData: VolsegEntryData }) {
    const state = useBehavior(entryData.currentState);
    const metadata = useBehavior(entryData.metadata);
    const allDescriptions = entryData.metadata.value!.allDescriptions;
    const entryDescriptions = allDescriptions.filter(d => d.target_kind === 'entry');
    const parsedSelectedSegmentKey = parseSegmentKey(state.selectedSegment);
    const { segmentationId, kind } = parsedSelectedSegmentKey;
    const visibleModels = state.visibleModels.map(model => model.pdbId);
    const allPdbs = entryData.pdbs;

    useBehavior(entryData.currentTimeframe);
    const annotationsJson = metadata!.raw.annotation;
    return <>
        {/* Title */}
        <div style={{ fontWeight: 'bold', padding: 8, paddingTop: 6, paddingBottom: 4, overflow: 'hidden' }}>
            {metadata!.raw.annotation?.name ?? 'Unnamed Annotation'}
        </div>
        {entryDescriptions.length > 0 && entryDescriptions.map(e =>
            <EntryDescriptionUI key={e.id} entryDescriptionData={e}></EntryDescriptionUI>)}
        <Popup nested trigger={<button className="msp-btn msp-btn-block">Annotation Editor</button>} modal>
            <>
                <JSONEditorComponent jsonData={annotationsJson} entryData={entryData} />
            </>
        </Popup>
        {/* Fitted models */}
        {allPdbs && allPdbs.length > 0 && <ExpandGroup header='Fitted models in PDB' initiallyExpanded>
            {allPdbs.map(pdb =>
                <WaitingButton key={pdb} onClick={() => entryData.actionShowFittedModel(visibleModels.includes(pdb) ? [] : [pdb])}
                    style={{ fontWeight: visibleModels.includes(pdb) ? 'bold' : undefined, textAlign: 'left', marginTop: 1 }}>
                    {pdb}
                </WaitingButton>
            )}
        </ExpandGroup>}

        {/* Volume */}
        <VolumeControls entryData={entryData} />
        <SegmentationControls model={entryData} />

        {/* Descriptions */}
        <SelectedSegmentDescription model={entryData} targetSegmentationId={segmentationId} targetKind={kind}></SelectedSegmentDescription>
    </>;
}

function TimeFrameSlider({ entryData }: { entryData: VolsegEntryData }) {
    const timeInfo = entryData.metadata.value!.raw.grid.volumes.time_info;
    const timeInfoStart = timeInfo.start;
    const timeInfoValue = useBehavior(entryData.currentTimeframe);
    const timeInfoEnd = timeInfo.end;
    if (entryData.filesData) {
        if (entryData.filesData.query.time) {
            return null;
        }
    }
    if (timeInfoEnd === 0) return null;

    return <ControlRow label='Time Frame' control={
        <WaitingSlider min={timeInfoStart} max={timeInfoEnd} value={timeInfoValue} step={1}
            onChange={async v => {
                await entryData.updateProjectData(v);
            }}
        />}
    />;
}

function VolumeChannelControls({ entryData, volume }: { entryData: VolsegEntryData, volume: StateObjectCell<PluginStateObject.Volume.Data> }) {
    const projectDataTransform = volume.transform;

    if (!projectDataTransform) return null;
    const params: ProjectDataParamsValues = projectDataTransform.params;
    const channelId = params.channelId;
    const channelLabel = volume.obj!.label;
    const childRef = entryData.plugin.state.data.tree.children.get(projectDataTransform.ref).toArray()[0];
    const volumeRepresentation3DNode = entryData.findNodesByRef(childRef);
    const transform = volumeRepresentation3DNode.transform;
    if (!transform) return null;
    const volumeValues: SimpleVolumeParamValues = {
        volumeType: transform.state.isHidden ? 'off' : transform.params?.type.name as any,
        opacity: transform.params?.type.params.alpha,
    };

    return <ExpandGroup header={`${channelLabel}`}>
        <WaitingParameterControls params={SimpleVolumeParams} values={volumeValues} onChangeValues={async next => { await sleep(20); await entryData.actionUpdateVolumeVisual(next, channelId, transform); }} />
        <UpdateTransformControl state={entryData.plugin.state.data} transform={transform} customHeader='none' />
    </ExpandGroup>;
}


function _getVisualTransformFromProjectDataTransform(model: VolsegEntryData, projectDataTransform: any) {
    const childRef = model.plugin.state.data.tree.children.get(projectDataTransform.ref).toArray()[0];
    const segmentationRepresentation3DNode = findNodesByRef(model.plugin, childRef);
    const transform = segmentationRepresentation3DNode.transform;
    if (transform.params.descriptions) {
        const childChildRef = model.plugin.state.data.tree.children.get(segmentationRepresentation3DNode.transform.ref).toArray()[0];
        const t = findNodesByRef(model.plugin, childChildRef);
        return t.transform;
    } else {
        return transform;
    }
}
function SegmentationSetControls({ model, segmentation, kind }: { model: VolsegEntryData, segmentation: StateObjectCell<PluginStateObject.Volume.Data> | StateObjectCell<VolsegGeometricSegmentation> | StateObjectCell<VolsegMeshSegmentation>, kind: 'lattice' | 'mesh' | 'primitive' }) {
    const projectDataTransform = segmentation.transform;
    if (!projectDataTransform) return null;
    const params: ProjectLatticeSegmentationDataParamsValues | ProjectGeometricSegmentationDataParamsValues | ProjectMeshSegmentationDataParamsValues = projectDataTransform.params;

    const segmentationId = params.segmentationId;

    const transform = _getVisualTransformFromProjectDataTransform(model, projectDataTransform);
    if (!transform) return null;

    let opacity = undefined;
    if (transform.params?.type) {
        opacity = transform.params?.type.params.alpha;
    } else {
        opacity = transform.params.alpha;
    }
    return <ExpandGroup header={`${segmentationId}`}>
        <ControlRow label='Opacity' control={
            <WaitingSlider min={0} max={1} value={opacity} step={0.05} onChange={async v => await model.actionSetOpacity(v, segmentationId, kind)} />
        } />
        <DescriptionsList
            model={model} targetSegmentationId={segmentationId} targetKind={kind}
        ></DescriptionsList>

    </ExpandGroup>;
}

function VolumeControls({ entryData }: { entryData: VolsegEntryData }) {
    const h = useBehavior(entryData.state.hierarchy);
    if (!h) return null;
    const isBusy = useBehavior(entryData.plugin.behaviors.state.isBusy);
    if (isBusy) {
        return null;
    }
    return <>
        <ExpandGroup header='Volume data'>
            {h.volumes.map((v) => {
                const params: ProjectDataParamsValues = v.transform.params;
                return <VolumeChannelControls key={params.channelId} entryData={entryData} volume={v} />;
            })}
        </ExpandGroup>
    </>;
}

export function SegmentationControls({ model }: { model: VolsegEntryData }) {
    if (!model.metadata.value!.hasSegmentations()) {
        return null;
    }
    const h = useBehavior(model.state.hierarchy);
    if (!h) return null;
    const isBusy = useBehavior(model.plugin.behaviors.state.isBusy);
    if (isBusy) {
        return null;
    }
    return <>
        <ExpandGroup header='Segmentation data'>
            {h.segmentations.map((v) => {
                return <SegmentationSetControls key={v.transform.ref} model={model} segmentation={v} kind={'lattice'} />;
            })}
            {h.meshSegmentations.map((v) => {
                return <SegmentationSetControls key={v.transform.ref} model={model} segmentation={v} kind={'mesh'} />;
            })}
            {h.geometricSegmentations.map((v) => {
                return <SegmentationSetControls key={v.transform.ref} model={model} segmentation={v} kind={'primitive'} />;

            })}
        </ExpandGroup>
    </>;
}


type ComponentParams<T extends React.Component<any, any, any> | ((props: any) => JSX.Element)> =
    T extends React.Component<infer P, any, any> ? P : T extends (props: infer P) => JSX.Element ? P : never;

export function WaitingSlider({ value, onChange, ...etc }: { value: number, onChange: (value: number) => any } & ComponentParams<Slider>) {
    const [changing, sliderValue, execute] = useAsyncChange(value);

    return <Slider value={sliderValue} disabled={changing} onChange={newValue => execute(onChange, newValue)} {...etc} />;
}

export function WaitingButton({ onClick, ...etc }: { onClick: () => any } & ComponentParams<typeof Button>) {
    const [changing, _, execute] = useAsyncChange(undefined);

    return <Button disabled={changing} onClick={() => execute(onClick, undefined)} {...etc}>
        {etc.children}
    </Button>;
}

export function WaitingParameterControls<T extends PD.Params>({ values, onChangeValues, ...etc }: { values: PD.ValuesFor<T>, onChangeValues: (values: PD.ValuesFor<T>) => any } & ComponentParams<ParameterControls<T>>) {
    const [changing, currentValues, execute] = useAsyncChange(values);

    return <ParameterControls isDisabled={changing} values={currentValues} onChangeValues={newValue => execute(onChangeValues, newValue)} {...etc} />;
}

function useAsyncChange<T>(initialValue: T) {
    const [isExecuting, setIsExecuting] = useState(false);
    const [value, setValue] = useState(initialValue);
    const isMounted = useRef(false);

    useEffect(() => setValue(initialValue), [initialValue]);

    useEffect(() => {
        isMounted.current = true;
        return () => { isMounted.current = false; };
    }, []);

    const execute = useCallback(
        async (func: (val: T) => Promise<any>, val: T) => {
            setIsExecuting(true);
            setValue(val);
            try {
                await func(val);
            } catch (err) {
                if (isMounted.current) {
                    setValue(initialValue);
                }
                throw err;
            } finally {
                if (isMounted.current) {
                    setIsExecuting(false);
                }
            }
        },
        []
    );

    return [isExecuting, value, execute] as const;
}
