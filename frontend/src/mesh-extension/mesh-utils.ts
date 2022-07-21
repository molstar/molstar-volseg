/** Helper functions for manipulation with mesh data. */

import * as MS from './molstar-lib-imports';

import { MeshlistData } from './mesh-extension';


type MeshModificationParams = { shift?: [number, number, number], group?: number, invertSides?: boolean };

/** Modify mesh in-place */
export function modify(m: MS.Mesh, params: MeshModificationParams) {
    if (params.shift !== undefined){
        const [dx,dy,dz] = params.shift;
        let vertices = m.vertexBuffer.ref.value;
        for (let i = 0; i < vertices.length; i+=3) {
            vertices[i]   += dx;
            vertices[i+1] += dy;
            vertices[i+2] += dz;
        }
    }
    if (params.group !== undefined){
        let groups = m.groupBuffer.ref.value;
        for (let i = 0; i < groups.length; i++) {
            groups[i] = params.group;
        }
    }
    if (params.invertSides) {
        let indices = m.indexBuffer.ref.value;
        for (let i = 0; i < indices.length; i+=3) {
            [indices[i], indices[i+1]] = [indices[i+1], indices[i]];
        }
        let normals = m.normalBuffer.ref.value;
        for (let i = 0; i < normals.length; i++) {
            normals[i] *= -1;
        }
    }
}

/** Create a copy a mesh, possibly modified */
export function copy(m: MS.Mesh, modification?: MeshModificationParams): MS.Mesh {
    let nVertices = m.vertexCount;
    let nTriangles = m.triangleCount;
    let vertices = new Float32Array(m.vertexBuffer.ref.value);
    let indices = new Uint32Array(m.indexBuffer.ref.value);
    let normals = new Float32Array(m.normalBuffer.ref.value);
    let groups = new Float32Array(m.groupBuffer.ref.value);
    let result = MS.Mesh.create(vertices, indices, normals, groups, nVertices, nTriangles);
    if (modification){
        modify(result, modification);
    }
    return result;
}

/** Join more meshes into one */
export function concat(...meshes: MS.Mesh[]): MS.Mesh {
    let nVertices = sum(meshes.map(m=>m.vertexCount));
    let nTriangles = sum(meshes.map(m=>m.triangleCount));
    let vertices = concatArrays(Float32Array, meshes.map(m => m.vertexBuffer.ref.value));
    let normals = concatArrays(Float32Array, meshes.map(m => m.normalBuffer.ref.value));
    let groups = concatArrays(Float32Array, meshes.map(m => m.groupBuffer.ref.value));
    let newIndices = [];
    let offset = 0;
    for (const m of meshes){
        newIndices.push(m.indexBuffer.ref.value.map(i => i + offset));
        offset += m.vertexCount;
    }
    let indices = concatArrays(Uint32Array, newIndices);
    return MS.Mesh.create(vertices, indices, normals, groups, nVertices, nTriangles);
}

/** Create Mesh from MeshListData */
export function makeMeshFromData(data: MeshlistData, meshIndex?: number, group?: number): MS.Mesh{
    if (meshIndex !== undefined){
        let d = data.meshes[meshIndex];
        let nVertices = d.vertices.length;
        let nTriangles = d.triangles.length;
        let vertices = new Float32Array(d.vertices.flat());
        let indices = new Uint32Array(d.triangles.flat());
        let normals = new Float32Array(d.normals.flat());  // QUESTION: What are normals good for?
        let groups = new Float32Array(nVertices).fill(group ?? 0);  // QUESTION: What are groups good for? Something with mouse-picking but how?
        return MS.Mesh.create(vertices, indices, normals, groups, nVertices, nTriangles);
    } else {
        const meshes = data.meshes.map((m, i) => makeMeshFromData(data, i, group ?? m.mesh_id));
        return concat(...meshes);
    }
}

/** Example mesh - 1 triagle */
export function makeFakeMesh1(): MS.Mesh {
    const nVertices = 3;
    const nTriangles = 1;
    const vertices = new Float32Array([0,0,0, 1,0,0, 0,1,0]);
    const indices = new Uint32Array([0,1,2]);
    const normals = new Float32Array([0,0,1]);
    const groups = new Float32Array([0]);
    return MS.Mesh.create(vertices, indices, normals, groups, nVertices, nTriangles);
}

/** Example mesh - irregular tetrahedron */
export function makeFakeMesh4(): MS.Mesh {
    const nVertices = 4;
    const nTriangles = 4;
    const vertices = new Float32Array([0,0,0, 1,0,0, 0,1,0, 0,0,1]);
    const indices = new Uint32Array([0,2,1, 0,1,3, 1,2,3, 2,0,3]);
    const normals = new Float32Array([-1,-1,-1, 1,0,0, 0,1,0, 0,0,1]);  // QUESTION: What are normals good for?
    const groups = new Float32Array([0, 1, 2, 3]);  // QUESTION: What are groups good for? Something with mouse-picking but how?
    return MS.Mesh.create(vertices, indices, normals, groups, nVertices, nTriangles);
}

function sum(array: number[]): number{
    return array.reduce((a,b)=>a+b, 0);  // TODO is there really no function for this?!
}

function concatArrays<T extends MS.TypedArray>(t: new (len: number)=>T, arrays: T[]): T {
    const totalLength = arrays.map(a => a.length).reduce((a,b)=>a+b, 0);
    const result: T = new t(totalLength);
    let offset = 0;
    for (const array of arrays){
        result.set(array, offset);
        offset += array.length;
    }
    return result;
}

/** Generate random colors (in a cycle) */
export const ColorGenerator = function* () {
    const colors = shuffleArray(Object.values(MS.ColorNames));
    let i = 0;
    while (true) {
        yield colors[i];
        i++;
        if (i >= colors.length) i = 0;
    }
}();
function shuffleArray<T>(array: T[]): T[] {
    // Stealed from https://www.w3docs.com/snippets/javascript/how-to-randomize-shuffle-a-javascript-array.html
    let curId = array.length;
    // There remain elements to shuffle
    while (0 !== curId) {
        // Pick a remaining element
        let randId = Math.floor(Math.random() * curId);
        curId -= 1;
        // Swap it with the current element.
        let tmp = array[curId];
        array[curId] = array[randId];
        array[randId] = tmp;
    }
    return array;
}

