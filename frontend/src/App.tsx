import React, { CSSProperties, useEffect, useRef, useState } from 'react';
import { useBehavior } from 'molstar/lib/mol-plugin-ui/hooks/use-behavior';

import './App.css';
import 'molstar/lib/mol-plugin-ui/skin/light.scss';
import { AppModel } from './model/model';
import { Button, ButtonGroup, Checkbox, LinearProgress, CssBaseline, Divider, FormControlLabel, InputLabel, MenuItem, Select, Slider, TextField, Typography, Autocomplete } from '@mui/material';
import { createEntryId, splitEntryId } from './model/helpers';


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

    const example = useBehavior(model.exampleType);

    return <>
        <div style={{ display: 'flex', flexDirection: 'column', width: RightWidth, position: 'absolute', right: 0, top: 0, bottom: 0, padding: '8px 8px 8px 0', overflow: 'hidden', overflowY: 'auto' }}>
            <div style={{ marginBottom: 8 }}>
                <ButtonGroup fullWidth>
                    <Button variant={example === 'emdb' ? 'contained' : 'outlined'} onClick={() => model.loadExample('emdb')}>EMDB SFF</Button>
                    <Button variant={example === 'bioimage' ? 'contained' : 'outlined'} onClick={() => model.loadExample('bioimage')}>BioImage Archive</Button>
                    <Button variant={example === 'meshes' ? 'contained' : 'outlined'} onClick={() => model.loadExample('meshes')}>Meshes</Button>
                    <Button variant={example === 'meshStreaming' ? 'contained' : 'outlined'} onClick={() => model.loadExample('meshStreaming')}>Mesh Streaming</Button>
                    <Button variant={example === 'auto' ? 'contained' : 'outlined'} onClick={() => model.loadExample('auto')}>Auto</Button>
                </ButtonGroup>
            </div>

            {example === 'emdb' && <UIExampleEmdb model={model} />}
            {example === 'bioimage' && <UIExampleBioimage model={model} />}
            {example === 'meshes' && <UIExampleMeshes model={model} />}
            {example === 'meshStreaming' && <UIExampleMeshStreaming model={model} />}
            {example === 'auto' && <UIExampleAuto model={model} />}
        </div>
        {example === 'bioimage' && <img src='/emd-99999.png' alt='' style={{ width: '33%', position: 'absolute', right: 8, bottom: 8, border: '1px solid #777' }} />}
        <MolStar model={model} />
    </>;
}

function UIExampleEmdb({ model }: { model: AppModel }) {
    const annotation = useBehavior(model.annotation);
    const current = useBehavior(model.currentSegment);

    return <>
        <EntryForm model={model} action={entryId => model.loadExample('emdb', entryId)} />

        <StatusBar model={model} />

        <EntryDetails model={model} />

        {annotation && <>
            <Typography variant='h6' style={{ marginTop: 8 }}>Segmentation</Typography>
            <Button variant={current ? 'outlined' : 'contained'} size='small' onClick={() => model.session?.showSegments(annotation?.segment_list ?? [])}>Show All</Button>
            {annotation?.segment_list.map((seg) =>
                <Button size='small' key={seg.id} style={{ marginTop: 4 }} variant={current === seg ? 'contained' : 'outlined'}
                    onClick={() => model.session?.showSegments([seg])}>
                    {seg.biological_annotation.name ?? `(Unnamed segment ${seg.id})`}
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
        <StatusBar model={model} style={{ marginBlock: 8, height: 6, borderRadius: 3 }} />
        <Typography variant='h6'>Benchmark Airyscan data matching FIB SEM data deposited on EMPIAR</Typography>
        <a href='https://www.ebi.ac.uk/biostudies/studies/S-BSST707' target='_blank' rel='noreferrer'>Archive Link</a>
        <Divider style={{ margin: '8px 0' }} />
        <InputLabel style={{ marginTop: 6, marginBottom: -6 }}>Isovalue</InputLabel>
        <Slider min={-1} max={-0.35} step={0.025} value={iso} valueLabelDisplay='auto' marks onChange={(_, v) => setIso(v as number)} onChangeCommitted={(_, v) => model.session?.setIsoValue(v as number, segm)} />
        <FormControlLabel control={<Checkbox value={segm} onChange={e => { setSegm(!!e.target.checked); model.session?.setIsoValue(iso, !segm); }} />} label='Auto-segmentation' />
        <Typography variant='body1' style={{ textAlign: 'center', marginTop: 16 }}>
            <b>~500kB of volumetric data</b> to create this rendering.<br />Obtained by converting 600MB of downsampled TIFFs from EMPIAR to MAP (using imod), original dataset size 1.7TB.
        </Typography>
    </>;
}

function UIExampleMeshes({ model }: { model: AppModel }) {
    const entryId = useBehavior(model.entryId);
    const annotation = useBehavior(model.annotation);
    const current = useBehavior(model.currentSegment);

    return <>
        <EntryForm model={model} action={entryId => model.loadExample('meshes', entryId)} />
        <StatusBar model={model} />
        <EntryDetails model={model} />

        {annotation && <>
            <Button variant={current ? 'outlined' : 'contained'} size='small'
                onClick={() => model.session?.showMeshSegments(annotation?.segment_list ?? [], entryId)}>
                Show All
            </Button>
            {annotation?.segment_list.map(seg =>
                <Button size='small' key={seg.id} style={{ marginTop: 4 }} variant={current === seg ? 'contained' : 'outlined'}
                    onClick={() => model.session?.showMeshSegments([seg], entryId)}>
                    {seg.id}. {seg.biological_annotation.name}
                </Button>
            )}
            <Typography variant='caption' marginTop={2}>
                If you are viewing "empiar-10070", two "background" segments are artificially removed.
            </Typography>
        </>
        }
    </>;
}

function UIExampleMeshStreaming({ model }: { model: AppModel }) {
    return <>
        <EntryForm model={model} action={entryId => model.loadExample('meshStreaming', entryId)} />
        <StatusBar model={model} />
        <EntryDetails model={model} />
    </>;
}

function UIExampleAuto({ model }: { model: AppModel }) {
    const pdbs = useBehavior(model.pdbs);
    const current = useBehavior(model.currentPdb);

    return <>
        <Typography variant='caption'>
            This example shows volume isosurface, lattice segmentation, mesh streaming, and/or fitted PDB models, depending on what data are available.
        </Typography>
        <Typography variant='caption'>
            Try: EMDB 1832 (lattice), EMDB 1181 (lattice+PDB), EMPIAR 10070 (mesh).
        </Typography>
        <Divider style={{ marginBlock: 16 }} />

        <EntryForm model={model} action={entryId => model.loadExample('auto', entryId)} />
        <StatusBar model={model} />
        <EntryDetails model={model} />

        {pdbs.length > 0 &&
            <div>
                <Typography variant='body2' style={{ marginTop: 12, marginBottom: 4 }}>Fitted models in PDB:</Typography>
                {pdbs.map(pdb =>
                    <Button key={pdb} size='small' variant={pdb === current ? 'contained' : 'outlined'} style={{ margin: 2, textTransform: 'lowercase' }}
                        title={pdb === current ? `Remove ${pdb}` : `Load ${pdb}`}
                        onClick={() => model.session?.showPdb(pdb === current ? undefined : pdb)}>
                        {pdb}
                    </Button>)}
            </div>
        }

    </>;
}

function EntryForm({ model, action }: { model: AppModel, action: (entryId: string) => any }) {
    const [source, setSource] = useState('');
    const [entryNumber, setEntryNumber] = useState('');
    // const [comboValues, setComboValues] = useState(['1014', '1181', '1547', '1832', '10070']); // TODO useBehavior, get from API
    const entryList = useBehavior(model.entryList);
    const comboValues = entryList[source]?.map(entry => splitEntryId(entry).entryNumber) ?? [];

    const entryId = useBehavior(model.entryId);
    const status = useBehavior(model.status);
    useEffect(() => {
        const form = splitEntryId(entryId);
        setSource(form.source ?? '');
        setEntryNumber(form.entryNumber ?? '');
    }, [entryId]);

    return <>
        <form onSubmit={e => { e.preventDefault(); action(createEntryId(source, entryNumber)); }} >
            <InputLabel>Source</InputLabel>
            <Select id='input-source' label='Source' value={source} onChange={e => setSource(e.target.value)} size='small' fullWidth style={{ marginBottom: 8 }}>
                <MenuItem value='empiar'>EMPIAR</MenuItem>
                <MenuItem value='emdb'>EMDB</MenuItem>
            </Select>

            {/* <InputLabel>Entry ID</InputLabel>
            <TextField id='input-entry-id' value={entryNumber} onChange={e => setEntryNumber(e.target.value)} size='small' fullWidth style={{ marginBottom: 8 }} /> */}

            <InputLabel>Entry ID</InputLabel>
            <Autocomplete size='small' fullWidth style={{ marginBottom: 8 }}
                disablePortal
                freeSolo // allow non-listed values
                selectOnFocus
                id='combo-entry-id'
                options={comboValues}
                inputValue={entryNumber}
                value={entryNumber}
                onInputChange={(e, value) => { setEntryNumber(value ?? ''); }}
                onChange={(e, value) => { action(createEntryId(source, value ?? '')); }}
                renderInput={(params) => <TextField {...params} />}
            />
            <Button type='submit' variant='contained' fullWidth disabled={status === 'loading'}>Load</Button>
        </form>
    </>;
}

function StatusBar({ model, style }: { model: AppModel, style?: CSSProperties }) {
    const status = useBehavior(model.status);
    return <div>
        <LinearProgress variant={status === 'loading' ? 'indeterminate' : 'determinate'} value={100} color={status === 'error' ? 'error' : 'primary'} style={{ marginBlock: 16, ...style }} />
    </div>
}

function EntryDetails({ model }: { model: AppModel }) {
    const entryId = useBehavior(model.entryId);
    const annotation = useBehavior(model.annotation);
    const error = useBehavior(model.error);

    if (error) {
        return <>
            <Typography variant='caption'>{entryId}</Typography>
            <Typography variant='h6' color='error'>Error</Typography>
            <Typography variant='body1' color='error'>{error.toString()}</Typography>
        </>;
    } else if (annotation) {
        return <>
            <Typography variant='caption'>{entryId}</Typography>
            <Typography variant='h6'>{annotation?.name ?? 'Untitled'}</Typography>
            <Typography variant='caption'>{annotation?.details}</Typography>
        </>;
    } else {
        return <Typography variant='caption'>{entryId}</Typography>;
    }

}

function MolStar({ model }: { model: AppModel }) {
    const target = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!target.current) return;
        model.init(target.current!);
    }, [model]);

    return <div ref={target} style={{ position: 'absolute', top: 0, bottom: 0, left: 0, right: RightWidth + 16 }} />;
}
