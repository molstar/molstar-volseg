import React, { useEffect, useRef } from 'react';
import { useBehavior } from 'molstar/lib/mol-plugin-ui/hooks/use-behavior';

import './App.css';
import 'molstar/lib/mol-plugin-ui/skin/light.scss';
import { AppModel } from './model';
import { Button } from '@mui/material';


function App() {
    return (
        <div className="App">
            <Main />
        </div>
    );
}

export default App;

function Main() {
    const _model = useRef<AppModel>();
    if (!_model.current) _model.current = new AppModel();
    const model = _model.current;
    const segments = useBehavior(model.segments);
    const current = useBehavior(model.currentSegment);


    return <>
        <MolStar model={model} />
        {/* <Button onClick={() => model.load()}>Load</Button> */}
        <div style={{ display: 'flex', flexDirection: 'column', width: 140, position: 'absolute', right: 8, top: 8 }}>
            {segments.map((id) => <Button key={id} variant={current === id ? 'contained' : 'text'} onClick={() => model.showSegmentLevel(id)}>Segment {id}</Button>)}
        </div>
    </>;
}

function MolStar({ model }: { model: AppModel }) {
    const target = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!target.current) return;
        model.init(target.current!);
    }, [model]);

    return <div ref={target} style={{ position: 'absolute', top: 0, bottom: 0, left: 0, right: 156 }} />;
}
