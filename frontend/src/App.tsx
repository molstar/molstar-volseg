import React, { useEffect, useRef, useState } from 'react';
import { useBehavior } from 'molstar/lib/mol-plugin-ui/hooks/use-behavior';

import './App.css';
import 'molstar/lib/mol-plugin-ui/skin/light.scss';
import { AppModel } from './model';
import { Button, ButtonGroup, Checkbox, CssBaseline, Divider, FormControlLabel, InputLabel, MenuItem, Select, Slider, TextField, Typography } from '@mui/material';


function App() {
    return (
        <div className="App">
            <CssBaseline>
                <Main />
            </CssBaseline>
        </div>
    );
}

export default App;

const RightWidth = 360;

function Main() {
    const _model = useRef<AppModel>();
    if (!_model.current) _model.current = new AppModel();
    const model = _model.current;

    const src = useBehavior(model.dataSource);


    return <>
        <div style={{ display: 'flex', flexDirection: 'column', width: RightWidth, position: 'absolute', right: 0, top: 0, bottom: 0, padding: '8px 8px 8px 0', overflow: 'hidden', overflowY: 'auto' }}>
            <div style={{ marginBottom: 8 }}>
                <ButtonGroup fullWidth>
                    <Button variant={src === 'xEmdb' ? 'contained' : 'outlined'} onClick={() => model.loadExampleEmdb('empiar-10070')}>EMDB SFF</Button>
                    <Button variant={src === 'xBioimage' ? 'contained' : 'outlined'} onClick={() => model.loadExampleBioimage()}>BioImage Archive</Button>
                    <Button variant={src === 'xMeshes' ? 'contained' : 'outlined'} onClick={() => model.loadExampleMeshes()}>Meshes</Button>
                    <Button variant={src === 'xMeshStreaming' ? 'contained' : 'outlined'} onClick={() => model.loadExampleMeshStreaming()}>Mesh Streaming</Button>
                </ButtonGroup>
            </div>
            {src === 'xEmdb' && <UIExampleEmdb model={model} />}
            {src === 'xBioimage' && <UIExampleBioimage model={model} />}
            {src === 'xMeshes' && <UIExampleMeshes model={model} />}
            {src === 'xMeshStreaming' && <UIExampleMeshStreaming model={model} />}
        </div>
        {src === 'xBioimage' && <img src='/emd-99999.png' alt='' style={{ width: '33%', position: 'absolute', right: 8, bottom: 8, border: '1px solid #777' }} />}
        <MolStar model={model} />
    </>;
}

function UIExampleMeshes({ model }: { model: AppModel }) {
    const entryId = useBehavior(model.entryId);
    const annotation = useBehavior(model.annotation);
    const current = useBehavior(model.currentSegment);
    const error = useBehavior(model.error);
    let form = model.splitEntryId(entryId);


    return <>
        <form onSubmit={(e) => { model.loadExampleMeshes(model.createEntryId(form.source, form.entryNumber)); e.preventDefault(); }} >
            <InputLabel>Source</InputLabel>
            <Select id='input-source' label='Source' defaultValue={form.source} onChange={(e) => { form.source = e.target.value; }} size='small' fullWidth style={{ marginBottom: 8 }}>
                <MenuItem value='empiar'>EMPIAR</MenuItem>
                <MenuItem value='emdb'>EMDB</MenuItem>
            </Select>

            <InputLabel>Entry ID</InputLabel>
            <TextField id='input-entry-id' defaultValue={form.entryNumber} onChange={(e) => { form.entryNumber = e.target.value; }} size='small' fullWidth style={{ marginBottom: 8 }} />

            <Button type='submit' variant='contained' fullWidth>Load</Button>
        </form>
        <Divider style={{ marginBlock: 16 }} />

        <Typography variant='caption'>{entryId}</Typography>

        {error && <>
            <Typography variant='h6'>{'Error'}</Typography>
            <Typography variant='body1'>
                {error.toString()}
            </Typography>
        </> || <>
                <Typography variant='h6'>{annotation?.name ?? 'Untitled'}</Typography>
                <Button variant={current ? 'outlined' : 'contained'} size='small'
                    onClick={() => model.showMeshSegments(annotation?.segment_list ?? [], entryId)}>
                    Show All
                </Button>
                {annotation?.segment_list.map(seg =>
                    <Button size='small' key={seg.id} style={{ marginTop: 4 }} variant={current === seg ? 'contained' : 'outlined'}
                        onClick={() => model.showMeshSegments([seg], entryId)}>
                        {seg.id}. {seg.biological_annotation.name}
                    </Button>
                )}
                <Typography variant='body1' marginTop={2}>
                    If you are viewing "empiar-10070", two "background" segments are artificially removed.
                </Typography>
            </>}

    </>;
}

function UIExampleMeshStreaming({ model }: { model: AppModel }) {
    const entryId = useBehavior(model.entryId);
    const annotation = useBehavior(model.annotation);
    const current = useBehavior(model.currentSegment);
    const error = useBehavior(model.error);
    let form = model.splitEntryId(entryId);

    return <>
        <form onSubmit={(e) => { model.loadExampleMeshStreaming(model.createEntryId(form.source, form.entryNumber)); e.preventDefault(); }} >
            <InputLabel>Source</InputLabel>
            <Select id='input-source' label='Source' defaultValue={form.source} onChange={(e) => { form.source = e.target.value; }} size='small' fullWidth style={{ marginBottom: 8 }}>
                <MenuItem value='empiar'>EMPIAR</MenuItem>
                <MenuItem value='emdb'>EMDB</MenuItem>
            </Select>

            <InputLabel>Entry ID</InputLabel>
            <TextField id='input-entry-id' defaultValue={form.entryNumber} onChange={(e) => { form.entryNumber = e.target.value; }} size='small' fullWidth style={{ marginBottom: 8 }} />

            <Button type='submit' variant='contained' fullWidth>Load</Button>
        </form>
        <Divider style={{ marginBlock: 16 }} />

        <Typography variant='caption'>{entryId}</Typography>

        {error && <>
            <Typography variant='h6'>{'Error'}</Typography>
            <Typography variant='body1'>
                {error.toString()}
            </Typography>
        </> || <>
            <Typography variant='h6'>{annotation?.name ?? 'Untitled'}</Typography>
        </>}

    </>;
}

function UIExampleEmdb({ model }: { model: AppModel }) {
    const entryId = useBehavior(model.entryId);
    const annotation = useBehavior(model.annotation);
    const current = useBehavior(model.currentSegment);

    return <>
        {annotation && <>
            <Typography variant='caption'>{entryId}</Typography>
            <Typography variant='h6'>{annotation?.details}</Typography>
            <Typography variant='caption'>{annotation?.details}</Typography>
            <Divider style={{ margin: '8px 0' }} />
            <Typography variant='h6'>Segmentation</Typography>
            <Button variant={current ? 'outlined' : 'contained'} size='small' onClick={() => model.showSegments(annotation?.segment_list ?? [])}>Show All</Button>
            {annotation?.segment_list.map((seg) =>
                <Button size='small' key={seg.id} style={{ marginTop: 4 }} variant={current === seg ? 'contained' : 'outlined'}
                    onClick={() => model.showSegments([seg])}>
                    {seg.biological_annotation.name}
                </Button>)
            }
            <Divider style={{ margin: '8px 0' }} />
            {current && <Typography variant='h6'>{current.biological_annotation.name}</Typography>}
            {current && <div>
                {current.biological_annotation.external_references.map(r => <div key={r.id}>
                    <Typography variant='caption' style={{ marginBottom: 8 }}><b>{r.resource}:{r.accession}</b><br />{r.description}</Typography>
                </div>)}
            </div>}
        </>}
    </>;
}

function UIExampleBioimage({ model }: { model: AppModel }) {
    const [iso, setIso] = useState(-0.55);
    const [segm, setSegm] = useState(false);

    return <>
        <Typography variant='h6'>Benchmark Airyscan data matching FIB SEM data deposited on EMPIAR</Typography>
        <a href='https://www.ebi.ac.uk/biostudies/studies/S-BSST707' target='_blank' rel='noreferrer'>Archive Link</a>
        <Divider style={{ margin: '8px 0' }} />
        <Slider min={-1} max={-0.35} step={0.025} value={iso} valueLabelDisplay='auto' marks onChange={(_, v) => setIso(v as number)} onChangeCommitted={(_, v) => model.setIsoValue(v as number, segm)} />
        <FormControlLabel control={<Checkbox value={segm} onChange={e => { setSegm(!!e.target.checked); model.setIsoValue(iso, !segm); }} />} label='Auto-segmentation' />
        <Typography variant='body1' style={{ textAlign: 'center', marginTop: 16 }}>
            <b>~500kB of volumetric data</b> to create this rendering.<br />Obtained by converting 600MB of downsampled TIFFs from EMPIAR to MAP (using imod), original dataset size 1.7TB.
        </Typography>
    </>;
}

function MolStar({ model }: { model: AppModel }) {
    const target = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!target.current) return;
        model.init(target.current!);
    }, [model]);

    return <div ref={target} style={{ position: 'absolute', top: 0, bottom: 0, left: 0, right: RightWidth + 16 }} />;
}
