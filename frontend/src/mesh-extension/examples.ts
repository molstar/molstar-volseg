/** Testing examples for using mesh-extension.ts. */

import * as MS from './molstar-lib-imports';

import { ParseMeshlistTransformer, MeshShapeTransformer, MeshlistData } from './mesh-extension';


export const DB_URL = '/db';  // local
// DB_URL = 'http://sestra.ncbr.muni.cz/data/cellstar-sample-data/db';  // download


export async function runMeshExtensionExamples(plugin: MS.PluginUIContext, db_url: string = DB_URL) {
    console.time('TIME MESH EXAMPLES');
    // await runIsosurfaceExample(plugin, db_url);
    // await runMolsurfaceExample(plugin);

    // Focused Ion Beam-Scanning Electron Microscopy of mitochondrial reticulum in murine skeletal muscle: https://www.ebi.ac.uk/empiar/EMPIAR-10070/
    await runMeshExample(plugin, 'all', db_url);
    await runMeshExample(plugin, 'fg', db_url);
    await runMultimeshExample(plugin, 'fg', 'worst', db_url);

    console.timeEnd('TIME MESH EXAMPLES');
}

/** Example for downloading multiple separate segments, each containing 1 mesh. */
export async function runMeshExample(plugin: MS.PluginUIContext, segments: 'fg'|'all', db_url: string = DB_URL) {
    const detail = 2;  
    // QUESTION: Detail-1 constains no normals. Why?
    // TODO ensure normal are in the input data (or create fake normals???)
    
    const segmentIds = (segments === 'all') ? 
        [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,17]   // segment-16 has no detail-2
        : [1,2,3,4,5,6,7,8,9,10,11,12,   14,   17];  // segment-13 and segment-15 are quasi background

    for (let segmentId of segmentIds){
        createMeshFromUrl(plugin, `${db_url}/empiar-10070-mesh-rounded/segment-${segmentId}/detail-${detail}`, segmentId, detail, true, true);
    }
}

/** Example for downloading a single segment containing multiple meshes. */
export async function runMultimeshExample(plugin: MS.PluginUIContext, segments: 'fg'|'all', detailChoice: 'best'|'worst', db_url: string = DB_URL) {
    const detail = (detailChoice === 'best') ? '2' : 'worst';
    await createMeshFromUrl(plugin, `${db_url}/empiar-10070-multimesh-rounded/segments-${segments}/detail-${detail}`, 0, detail, false, true);
}

/** Download data and create state tree hierarchy down to visual representation. */
export async function createMeshFromUrl(plugin: MS.PluginUIContext, meshDataUrl: string, segmentId: number, detail: number|string, collapseTree: boolean, log: boolean) {

    // PARAMS - Depend on the type of transformer T -> Params<T>
    // 1st argument to plugin.builders.data.rawData, 2nd argument to .apply
    // Params<RawData>: {  // src/mol-plugin-state/transforms/data.ts: 143
    //     data: PD.Value<string | number[] | ArrayBuffer | Uint8Array>('', { isHidden: true }),
    //     label: PD.Optional(PD.Text(''))
    // }

    // OPTIONS - Same for each type of transformer
    // Last argument to plugin.builders.data.rawData, plugin.builders.data.download, .apply
    // interface StateTransform.Options {
    //     ref?: string,  // State tree node ID (default: auto-generated ID)
    //     tags?: string | string[],  // I don't know what this is for
    //     state?: {
    //         isGhost?: boolean,  // is the cell shown in the UI
    //         isLocked?: boolean,  // can the corresponding be deleted by the user.
    //         isHidden?: boolean,  // is the representation associated with the cell hidden
    //         isCollapsed?: boolean,  // is the tree node collapsed?
    //     },
    //     dependsOn?: string[]  // references to other nodes, I think
    // }

    // RAW DATA NODE
    const rawDataNode = await plugin.builders.data.download(
        { url: meshDataUrl, isBinary: false, label: `Downloaded Data ${segmentId}` },  // params
        { ref: `ref-raw-data-node-${segmentId}`, tags: ['What', 'are', 'tags', 'good', 'for?'], state: {isCollapsed: collapseTree}}  // options  // QUESTION: what are tags good for?
    );
    if (log) console.log('rawDataNode:', rawDataNode);

    // PARSED DATA NODE
    const parsedDataNode = await plugin.build().to(rawDataNode).apply(
        ParseMeshlistTransformer,
        { label: undefined, segmentName: `Segment ${segmentId}`, detail: detail.toString() },  // params
        { ref: `ref-parsed-data-node-${segmentId}` }  // options
    ).commit();
    if (log) console.log('parsedDataNode:', parsedDataNode);
    if (log) console.log('parsedDataNode.data:', parsedDataNode.data);
    if (log) console.log('parsedDataNode mesh list stats:\n', MeshlistData.stats(parsedDataNode.data!));

    // MESH SHAPE NODE
    const shapeNode = await plugin.build().to(parsedDataNode).apply(MeshShapeTransformer, 
        {},  // options
        { ref: `ref-shape-node-${segmentId}` }
    ).commit();
    if (log) console.log('shapeNode:', shapeNode);
    if (log) console.log('shapeNode.data:', shapeNode.data);

    // MESH REPR NODE
    const reprNode = await plugin.build().to(shapeNode).apply(MS.ShapeRepresentation3D,
        {},
        { ref: `ref-repr-nod+e${segmentId}` }
    ).commit();
    if (log) console.log('reprNode:', reprNode);
    if (log) console.log('reprNode.data:', reprNode.data);

}

/** Example for downloading a protein structure and visualizing molecular surface. */
export async function runMolsurfaceExample(plugin: MS.PluginUIContext) {
    const entryId = 'pdb-7etq';

    // Node "https://www.ebi.ac.uk/pdbe/entry-files/download/7etq.bcif" ("transformer": "ms-plugin.download") -> var data
    const data = await plugin.builders.data.download({ url: 'https://www.ebi.ac.uk/pdbe/entry-files/download/7etq.bcif', isBinary: true }, { state: { isGhost: false } });
    console.log('formats:', plugin.dataFormats.list);

    // Node "CIF File" ("transformer": "ms-plugin.parse-cif")
    // Node "7ETQ 1 model" ("transformer": "ms-plugin.trajectory-from-mmcif") -> var trajectory
    const parsed = await plugin.dataFormats.get('mmcif')!.parse(plugin, data, { entryId });
    const trajectory: MS.StateObjectSelector<MS.PluginStateObject.Molecule.Trajectory> = parsed.trajectory;
    console.log('parsed', parsed);
    console.log('trajectory', trajectory);

    // Node "Model 1" ("transformer": "ms-plugin.model-from-trajectory") -> var model
    const model = await plugin.build().to(trajectory).apply(MS.StateTransforms.Model.ModelFromTrajectory).commit();
    console.log('model:', model);

    // Node "Model 91 elements" ("transformer": "ms-plugin.structure-from-model") -> var structure
    const structure = await plugin.build().to(model).apply(MS.StateTransforms.Model.StructureFromModel,).commit();
    console.log('structure:', structure);

    // Node "Molecular Surface" ("transformer": "ms-plugin.structure-representation-3d") -> var repr
    const reprParams = MS.createStructureRepresentationParams(plugin, undefined, { type: 'molecular-surface' });
    const repr = await plugin.build().to(structure).apply(MS.StateTransforms.Representation.StructureRepresentation3D, reprParams).commit();
    console.log('repr:', repr);

    // TODO try to steal from PLY repr?

    // plugin.build().to(repr).apply(MS.StateTransforms.Representation.VolumeRepresentation3D)
}

/** Example for downloading an EMDB density data and visualizing isosurface. */
export async function runIsosurfaceExample(plugin: MS.PluginUIContext, db_url: string = DB_URL) {
    const entryId = 'emd-1832';
    const isoLevel = 2.73;

    let root = await plugin.build();
    const data = await plugin.builders.data.download({ url: `${db_url}/emd-1832-box`, isBinary: true }, { state: { isGhost: false } });
    const parsed = await plugin.dataFormats.get('dscif')!.parse(plugin, data, { entryId });

    const volume: MS.StateObjectSelector<MS.PluginStateObject.Volume.Data> = parsed.volumes?.[0] ?? parsed.volume;
    const volumeData = volume.cell!.obj!.data;
    console.log('data:', data);
    console.log('parsed:', parsed);
    console.log('volume:', volume);
    console.log('volumeData:', volumeData);

    root = await plugin.build();
    console.log('root:', root);
    console.log('to:', root.to(volume));
    console.log('toRoot:', root.toRoot());

    let volumeParams;
    volumeParams = MS.createVolumeRepresentationParams(plugin, volumeData, {
        type: 'isosurface',
        typeParams: {
            alpha: 0.5,
            isoValue: MS.Volume.adjustedIsoValue(volumeData, isoLevel, 'relative'),
            visuals: ['solid'],
            sizeFactor: 1,
        },
        color: 'uniform',
        colorParams: { value: MS.Color(0x00aaaa) },

    });
    root.to(volume).apply(MS.StateTransforms.Representation.VolumeRepresentation3D, volumeParams);

    volumeParams = MS.createVolumeRepresentationParams(plugin, volumeData, {
        type: 'isosurface',
        typeParams: {
            alpha: 1.0,
            isoValue: MS.Volume.adjustedIsoValue(volumeData, isoLevel, 'relative'),
            visuals: ['wireframe'],
            sizeFactor: 1,
        },
        color: 'uniform',
        colorParams: { value: MS.Color(0x8800aa) },

    });
    root.to(volume).apply(MS.StateTransforms.Representation.VolumeRepresentation3D, volumeParams);
    await root.commit();
}
