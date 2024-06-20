# Mol* Volumes & Segmentations
Mol\* Volumes & Segmentations 2.0 (Mol\* VS 2.0) is a next iteration of web application designed for real-time visualization of large-scale volumetric, segmentation, and annotation data.

# Running Mol\* viewer with Mol* Volumes & Segmentations extension

1. Create new folder, e.g.:
```sh
mkdir molstar-volseg-viewer
```
2. Change directory to it, e.g.:
```sh
cd molstar-volseg-viewer
```
3. Initialize new npm package:
```sh
npm init
```
4. Install Mol\* and Mol* Volumes & Segmentations extension npm packages:
```
npm install molstar
npm install molstar-volseg
```

5. Create `index.html` file in `molstar-volseg-viewer` with the following content:
```html
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, user-scalable=no, minimum-scale=1.0, maximum-scale=1.0">
        <link rel="icon" href="./favicon.ico" type="image/x-icon">
        <title>Mol* Viewer</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            html, body {
                width: 100%;
                height: 100%;
                overflow: hidden;
            }
            hr {
                margin: 10px;
            }
            h1, h2, h3, h4, h5 {
                margin-top: 5px;
                margin-bottom: 3px;
            }
            button {
                padding: 2px;
            }
            #app {
                position: absolute;
                left: 100px;
                top: 100px;
                width: 800px;
                height: 600px;
            }
        </style>
        <link rel="stylesheet" type="text/css" href="molstar.css" />
    </head>
    <body>
        <div id="app"></div>
        <script type="module">
            import * as molstar from './molstar.mjs';
            console.log('imported molstar.mjs');
            console.log(molstar);
            function getParam(name, regex) {
                var r = new RegExp(name + '=' + '(' + regex + ')[&]?', 'i');
                return decodeURIComponent(((window.location.search || '').match(r) || [])[1] || '');
            }

            var debugMode = getParam('debug-mode', '[^&]+').trim() === '1';
            if (debugMode) molstar.setDebugMode(debugMode);

            var timingMode = getParam('timing-mode', '[^&]+').trim() === '1';
            if (timingMode) molstar.setTimingMode(timingMode);

            var hideControls = getParam('hide-controls', '[^&]+').trim() === '1';
            var collapseLeftPanel = getParam('collapse-left-panel', '[^&]+').trim() === '1';
            var pdbProvider = getParam('pdb-provider', '[^&]+').trim().toLowerCase();
            var emdbProvider = getParam('emdb-provider', '[^&]+').trim().toLowerCase();
            var mapProvider = getParam('map-provider', '[^&]+').trim().toLowerCase();
            var pixelScale = getParam('pixel-scale', '[^&]+').trim();
            var pickScale = getParam('pick-scale', '[^&]+').trim();
            var pickPadding = getParam('pick-padding', '[^&]+').trim();
            var transparency = getParam('transparency', '[^&]+').trim().toLowerCase();
            var preferWebgl1 = getParam('prefer-webgl1', '[^&]+').trim() === '1' || void 0;
            var allowMajorPerformanceCaveat = getParam('allow-major-performance-caveat', '[^&]+').trim() === '1';
            var powerPreference = getParam('power-preference', '[^&]+').trim().toLowerCase();

            // console.log('Available extensions: ', Object.keys(molstar.ExtensionMap));

            molstar.Viewer.create('app', {
                disabledExtensions: [], // anything from Object.keys(molstar.ExtensionMap)
                layoutShowControls: !hideControls,
                viewportShowExpand: false,
                collapseLeftPanel: collapseLeftPanel,
                pdbProvider: pdbProvider || 'pdbe',
                emdbProvider: emdbProvider || 'pdbe',
                volumeStreamingServer: (mapProvider || 'pdbe') === 'rcsb'
                    ? 'https://maps.rcsb.org'
                    : 'https://www.ebi.ac.uk/pdbe/densities',
                pixelScale: parseFloat(pixelScale) || 1,
                pickScale: parseFloat(pickScale) || 0.25,
                pickPadding: isNaN(parseFloat(pickPadding)) ? 1 : parseFloat(pickPadding),
                transparency: transparency || undefined,
                preferWebgl1: preferWebgl1,
                allowMajorPerformanceCaveat: allowMajorPerformanceCaveat,
                powerPreference: powerPreference || 'high-performance',
            }).then(viewer => {
                var snapshotId = getParam('snapshot-id', '[^&]+').trim();
                if (snapshotId) viewer.setRemoteSnapshot(snapshotId);

                var snapshotUrl = getParam('snapshot-url', '[^&]+').trim();
                var snapshotUrlType = getParam('snapshot-url-type', '[^&]+').toLowerCase().trim() || 'molj';
                if (snapshotUrl && snapshotUrlType) viewer.loadSnapshotFromUrl(snapshotUrl, snapshotUrlType);

                var structureUrl = getParam('structure-url', '[^&]+').trim();
                var structureUrlFormat = getParam('structure-url-format', '[a-z]+').toLowerCase().trim();
                var structureUrlIsBinary = getParam('structure-url-is-binary', '[^&]+').trim() === '1';
                if (structureUrl) viewer.loadStructureFromUrl(structureUrl, structureUrlFormat, structureUrlIsBinary);

                var mvsUrl = getParam('mvs-url', '[^&]+').trim();
                var mvsData = getParam('mvs-data', '[^&]+').trim();
                var mvsFormat = getParam('mvs-format', '[^&]+').trim() || 'mvsj';
                if (mvsUrl && mvsData) console.error('Cannot specify mvs-url and mvs-data URL parameters at the same time. Ignoring both.');
                else if (mvsUrl) viewer.loadMvsFromUrl(mvsUrl, mvsFormat);
                else if (mvsData) viewer.loadMvsData(mvsData, mvsFormat);
                
                var cvsxUrl = getParam('cvsx-url', '[^&]+').trim();
                var cvsxFormat = getParam('cvsx-format', '[^&]+').trim() || 'cvsx';
                if (cvsxUrl) viewer.loadCvsxFromUrl(cvsxUrl, cvsxFormat)

                var pdb = getParam('pdb', '[^&]+').trim();
                if (pdb) viewer.loadPdb(pdb);

                var pdbDev = getParam('pdb-dev', '[^&]+').trim();
                if (pdbDev) viewer.loadPdbDev(pdbDev);

                var emdb = getParam('emdb', '[^&]+').trim();
                if (emdb) viewer.loadEmdb(emdb);

                var afdb = getParam('afdb', '[^&]+').trim();
                if (afdb) viewer.loadAlphaFoldDb(afdb);

                var modelArchive = getParam('model-archive', '[^&]+').trim();
                if (modelArchive) viewer.loadModelArchive(modelArchive);

                window.addEventListener('unload', () => {
                    // to aid GC
                    viewer.dispose();
                });
            });
        </script>
        <!-- __MOLSTAR_ANALYTICS__ -->
    </body>
</html>
```

6. Copy `molstar.mjs` and `molstar.css` files from `build` folder of `molstar-volseg` NPM package (`node_modules\molstar-volseg\build`) to `molstar-volseg-viewer`:
```sh
cp node_modules/molstar-volseg/build/molstar.css .
cp node_modules/molstar-volseg/build/molstar.mjs .
```



7. Install `http-server` NPM module
```sh
npm install http-server
```

8. Serve the `index.html` webpage using `http-server`. From `molstar-volseg-viewer` directory run:

```sh
http-server
```
It will serve the webpage with Mol* Viewer with Mol* Volumes & Segmentations extension at `http://127.0.0.1:8080` by default.

