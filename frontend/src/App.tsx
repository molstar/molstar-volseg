import React, { useEffect, useRef } from 'react';
import { createPluginUI } from 'molstar/lib/mol-plugin-ui/react18';

import './App.css';
import 'molstar/lib/mol-plugin-ui/skin/light.scss';


function App() {
  return (
    <div className="App">
      <MolStar />
    </div>
  );
}

export default App;

function MolStar() {
  const target = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!target.current) return;
    createPluginUI(target.current!)
  }, []);

  return <div ref={target} style={{ position: 'relative', width: 640, height: 480 }} />;
}
