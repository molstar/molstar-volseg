/** Defines new types of State tree transformers for dealing with mesh data. */

import * as MS from './molstar-lib-imports';
import PD = MS.ParamDefinition;

import * as MeshUtils from './mesh-utils';


const CellStarTransform: MS.StateTransformer.Builder.Root = MS.StateTransformer.builderFactory('cellstar');


/////////////////////////////////////////////////////////////////////////////////////////////////////
// Parsed data

/** Data for a single mesh */
interface MeshData {
    mesh_id: number,
    triangles: [number, number, number][],
    normals: [number, number, number][],
    vertices: [number, number, number][],
}

/** Data type for MeshlistStateObject - list of meshes */
export interface MeshlistData {
    segmentName: string,
    detail: string,
    meshes: MeshData[],
}

export namespace MeshlistData {
    export function stats(meshListData: MeshlistData): string {
        let lines = [`Meshlist "${meshListData.segmentName}" (detail ${meshListData.detail}) [${meshListData.meshes.length}]:`];
        for (let meshData of meshListData.meshes) {
            lines.push(`    { mesh_id: ${meshData.mesh_id}, vertices: ${meshData.vertices.length}, normals: ${meshData.normals?.length}, triangles: ${meshData.triangles.length} }`);
        }
        return lines.join('\n');
    }

    export function validate(obj: MeshData[]): string {
        return validateType(obj, Array.isArray, '$', 'array')
            || obj.map(x => validateMeshData(x)).find(s => s)
            || '';
        // TODO there must be a better way of validating if all field are present and have correct type
    }

    function validateMeshData(obj: MeshData): string {
        return [
            validateType(obj.mesh_id, x => typeof x === 'number', '$[i].mesh_id', () => 'number'),
            validateType(obj.vertices, Array.isArray, '$[i].vertices', 'number[][]'),
            validateType(obj.triangles, Array.isArray, '$[i].triangles', 'number[][]'),
        ].find(s => s) ?? '';
    }

    function validateType(obj: any, valFunc: (obj: any) => boolean, objRef: string | (() => string), typeRef: string | (() => string)): string {
        if (valFunc(obj)) {
            return '';
        } else {
            const objRefStr = (typeof objRef === 'string') ? objRef : objRef();
            const typeRefStr = (typeof typeRef === 'string') ? typeRef : typeRef();
            return `${objRefStr} must be ${typeRefStr}, not ${typeof obj}`;
        }
    }
}


/////////////////////////////////////////////////////////////////////////////////////////////////////
// Raw Data -> Parsed data

export class MeshlistStateObject extends MS.PluginStateObject.Create<MeshlistData>({ name: 'Parsed Meshlist', typeClass: 'Object' }) { }
// QUESTION: is typeClass just for color, or does do something?

export const ParseMeshlistTransformer = CellStarTransform({
    name: 'meshlist-from-string',
    from: MS.PluginStateObject.Data.String,
    to: MeshlistStateObject,
    // These params are actually definition of what can be changed in the GUI!!!

    params: {
        label: PD.Text(MeshlistStateObject.type.name, { 'isHidden': true }),  // QUESTION: Is this the right way to pass a value to apply() without exposing it in GUI?
        segmentName: PD.Text('Segment'),
        detail: PD.Text('?', { 'isHidden': true }),
        // QUESTION: Is PD.Text better than PD.Value<string>? I saw it in Params<RawData>, src/mol-plugin-state/transforms/data.ts: 145
    }
})({
    apply({ a, params }, globalCtx) {  // a is the parent node, params are 2nd argument to To.apply(), globalCtx is the plugin 
        const origData: string = a.data;
        let parsedData: MeshData[];
        try {
            parsedData = JSON.parse(origData);
        }
        catch (err) {
            if (err instanceof SyntaxError) throw new Error(`ParseMeshlistTransformer apply(): Input data could not be parsed as JSON (${err})`);
            else throw err;
        }
        const validationMsg = MeshlistData.validate(parsedData);
        if (validationMsg) throw new Error(`ParseMeshlistTransformer apply(): Input data could be parsed as JSON, but are not valid as MeshlistData (${validationMsg}).`);

        const meshlistData: MeshlistData = {
            segmentName: params.segmentName,
            detail: params.detail,
            meshes: parsedData,
        }
        console.log('ParseMeshlistTransformer params:', params);
        console.log('ParseMeshlistTransformer stats:', MeshlistData.stats(meshlistData));
        const es = meshlistData.meshes.length === 1 ? '' : 'es';
        return new MeshlistStateObject(meshlistData, { label: params.label, description: `${meshlistData.segmentName} (${meshlistData.meshes.length} mesh${es})` });
        // QUESTION: Should I return Task? Is it better?
    }
});


/////////////////////////////////////////////////////////////////////////////////////////////////////
// Parsed data -> Shape

/** Data type for PluginStateObject.Shape.Provider */
type MeshShapeProvider = MS.ShapeProvider<MeshlistData, MS.Mesh, MS.Mesh.Params>;

/** Params for MeshShapeTransformer */
const meshShapeParamDef = {
    color: PD.Value<MS.Color|undefined>(undefined), // undefined means random color
}

const meshParamDef0 = MS.Mesh.Params;
const meshParamDef: MS.Mesh.Params = {
    // These are basically 
    // BaseGeometry.Params
    alpha: PD.Numeric(1, { min: 0, max: 1, step: 0.01 }, { label: 'Opacity', isEssential: true, description: 'How opaque/transparent the representation is rendered.' }),
    quality: PD.Select<MS.VisualQuality>('auto', MS.VisualQualityOptions, { isEssential: true, description: 'Visual/rendering quality of the representation.' }),
    material: MS.Material.getParam(),
    clip: MS.Mesh.Params.clip,  // PD.Group(MS.Clip.Params),
    instanceGranularity: PD.Boolean(false, { description: 'Use instance granularity for marker, transparency, clipping, overpaint, substance data to save memory.' }),
    // Mesh.Params
    doubleSided: PD.Boolean(false, MS.BaseGeometry.CustomQualityParamInfo),
    flipSided: PD.Boolean(false, MS.BaseGeometry.ShadingCategory),
    flatShaded: PD.Boolean(true, MS.BaseGeometry.ShadingCategory),  // CHANGED, default: false (set true to see the real mesh vertices and triangles)
    ignoreLight: PD.Boolean(false, MS.BaseGeometry.ShadingCategory),
    xrayShaded: PD.Boolean(false, MS.BaseGeometry.ShadingCategory),  // this is like better opacity (angle-dependent), nice
    transparentBackfaces: PD.Select('off', PD.arrayToOptions(['off', 'on', 'opaque']), MS.BaseGeometry.ShadingCategory),
    bumpFrequency: PD.Numeric(0, { min: 0, max: 10, step: 0.1 }, MS.BaseGeometry.ShadingCategory),
    bumpAmplitude: PD.Numeric(1, { min: 0, max: 5, step: 0.1 }, MS.BaseGeometry.ShadingCategory),
    // TODO when I change values here, it has effect, but not if I change them in GUI
};

export const MeshShapeTransformer = CellStarTransform({
    name: 'shape-from-meshlist',
    display: { name: 'Shape from Meshlist', description: 'Create Shape from Meshlist data' },
    from: MeshlistStateObject,
    to: MS.PluginStateObject.Shape.Provider,
    params: meshShapeParamDef
})({
    apply({ a, params }) {
        const origData = a.data;
        // you can look for example at ShapeFromPly in mol-plugin-state/tansforms/model.ts as an example
        const color = params.color ?? MeshUtils.ColorGenerator.next().value;
        const shapeProvider: MeshShapeProvider = {
            label: 'Mesh',
            data: origData,
            params: meshParamDef,  // TODO how to pass the real params correctly?
            geometryUtils: MS.Mesh.Utils,
            getShape: (ctx, data: MeshlistData) => {
                let mesh = MeshUtils.makeMeshFromData(data);
                MeshUtils.modify(mesh, { invertSides: true });  // QUESTION: vertex orientation convention is probably opposite in API and in MolStar -> TODO solve
                const meshShape: MS.Shape<MS.Mesh> = MS.Shape.create('MyShape', data, mesh,
                () => color, 
                () => 1, (group) => `${data.segmentName} | Detail ${data.detail} | Mesh ${group}`);
                return meshShape;
            }
        }
        return new MS.PluginStateObject.Shape.Provider(shapeProvider, { label: MS.PluginStateObject.Shape.Provider.type.name, description: a.description });
    }
});


/////////////////////////////////////////////////////////////////////////////////////////////////////
// Shape -> Repr

// type MeshRepr = MS.PluginStateObject.Representation3DData<MS.ShapeRepresentation<MS.ShapeProvider<any,any,any>, MS.Mesh, MS.Mesh.Params>, any>;

// export const CustomMeshReprTransformer = CellStarTransform({
//     name: 'custom-repr',
//     from: MS.PluginStateObject.Shape.Provider, // later we can change this
//     to: MS.PluginStateObject.Shape.Representation3D,
// })({
//     apply({ a }, globalCtx) {
//         const repr: MeshRepr = createRepr(a.data); // TODO implement createRepr
//         // have a look at MS.StateTransforms.Representation.ShapeRepresentation3D if you want to try implementing yourself
//         return new MS.PluginStateObject.Shape.Representation3D(repr)
//     },
// })

// export async function createMeshRepr(plugin: MS.PluginContext, data: any) {
//     await plugin.build()
//         .toRoot()
//         .apply(CreateMyShapeTransformer, { data })
//         .apply(MS.StateTransforms.Representation.ShapeRepresentation3D) // this should work
//         // or .apply(CustomMeshRepr)
//         .commit();
// }

// export function createRepr(reprData: MS.ShapeProvider<any,any,any>): MeshRepr {
//     throw new Error('NotImplemented');
//     return {} as MeshRepr;
// }
