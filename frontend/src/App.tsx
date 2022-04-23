import React, { useEffect, useRef, useState } from 'react';
import { useBehavior } from 'molstar/lib/mol-plugin-ui/hooks/use-behavior';

import './App.css';
import 'molstar/lib/mol-plugin-ui/skin/light.scss';
import { AppModel } from './model';
import { Button, ButtonGroup, CssBaseline, Divider, Slider, Typography } from '@mui/material';


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
        <MolStar model={model} />
        <div style={{ display: 'flex', flexDirection: 'column', width: RightWidth, position: 'absolute', right: 0, top: 0, bottom: 0, padding: '8px 8px 8px 0', overflow: 'hidden', overflowY: 'auto' }}>
            <div style={{ marginBottom: 8 }}>
                <ButtonGroup fullWidth>
                    <Button variant={src === '1832' ? 'contained' : 'outlined'} onClick={() => model.load1832()}>EMDB SFF</Button>
                    <Button variant={src === '99999' ? 'contained' : 'outlined'} onClick={() => model.load99999()}>BioImage Archive</Button>
                </ButtonGroup>
            </div>
            {src === '1832' && <UI1832 model={model} />}
            {src === '99999' && <UI99999 model={model} />}
        </div>
    </>;
}

function UI1832({ model }: { model: AppModel }) {
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
            {annotation?.segment_list.map((seg) => <Button size='small' key={seg.id} style={{ marginTop: 4 }} variant={current === seg ? 'contained' : 'outlined'} onClick={() => model.showSegments([seg])}>{seg.biological_annotation.name}</Button>)}
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

function UI99999({ model }: { model: AppModel }) {
    const [iso, setIso] = useState(-0.55);

    return <>
        <Typography variant='h6'>Benchmark Airyscan data matching FIB SEM data deposited on EMPIAR</Typography>
        <Divider style={{ margin: '8px 0' }} />
        <Slider min={-1} max={0.7} step={0.05} value={iso} valueLabelDisplay='auto' marks onChange={(_, v) => setIso(v as number)}  onChangeCommitted={(_, v) => model.setIsoValue(v as number)} />
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
