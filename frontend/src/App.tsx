import React, { useEffect, useRef } from 'react';
import { createPluginUI } from 'molstar/lib/mol-plugin-ui/react18';

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

    return <>
        <MolStar model={model} />
        {/* <Button onClick={() => model.load()}>Load</Button> */}
        {new Array(10).fill(0).map((_, v) => <Button key={v} onClick={() => model.showLevel(v)}>Segment {v}</Button>)}
    </>;
}

function MolStar({ model }: { model: AppModel }) {
    const target = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!target.current) return;
        model.init(target.current!);
    }, [model]);

    return <div ref={target} style={{ position: 'relative', width: 640, height: 480 }} />;
}
