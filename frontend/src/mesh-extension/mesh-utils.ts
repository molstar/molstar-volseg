/** Helper functions for manipulation with mesh data. */

import * as MS from './molstar-lib-imports';

import { MeshlistData } from './mesh-extension';


type MeshModificationParams = { shift?: [number, number, number], group?: number, invertSides?: boolean };

/** Modify mesh in-place */
export function modify(m: MS.Mesh, params: MeshModificationParams) {
    if (params.shift !== undefined) {
        const [dx, dy, dz] = params.shift;
        const vertices = m.vertexBuffer.ref.value;
        for (let i = 0; i < vertices.length; i += 3) {
            vertices[i] += dx;
            vertices[i + 1] += dy;
            vertices[i + 2] += dz;
        }
    }
    if (params.group !== undefined) {
        const groups = m.groupBuffer.ref.value;
        for (let i = 0; i < groups.length; i++) {
            groups[i] = params.group;
        }
    }
    if (params.invertSides) {
        const indices = m.indexBuffer.ref.value;
        for (let i = 0; i < indices.length; i += 3) {
            [indices[i], indices[i + 1]] = [indices[i + 1], indices[i]];
        }
        const normals = m.normalBuffer.ref.value;
        for (let i = 0; i < normals.length; i++) {
            normals[i] *= -1;
        }
    }
}

/** Create a copy a mesh, possibly modified */
export function copy(m: MS.Mesh, modification?: MeshModificationParams): MS.Mesh {
    const nVertices = m.vertexCount;
    const nTriangles = m.triangleCount;
    const vertices = new Float32Array(m.vertexBuffer.ref.value);
    const indices = new Uint32Array(m.indexBuffer.ref.value);
    const normals = new Float32Array(m.normalBuffer.ref.value);
    const groups = new Float32Array(m.groupBuffer.ref.value);
    const result = MS.Mesh.create(vertices, indices, normals, groups, nVertices, nTriangles);
    if (modification) {
        modify(result, modification);
    }
    return result;
}

/** Join more meshes into one */
export function concat(...meshes: MS.Mesh[]): MS.Mesh {
    const nVertices = sum(meshes.map(m => m.vertexCount));
    const nTriangles = sum(meshes.map(m => m.triangleCount));
    const vertices = concatArrays(Float32Array, meshes.map(m => m.vertexBuffer.ref.value));
    const normals = concatArrays(Float32Array, meshes.map(m => m.normalBuffer.ref.value));
    const groups = concatArrays(Float32Array, meshes.map(m => m.groupBuffer.ref.value));
    const newIndices = [];
    let offset = 0;
    for (const m of meshes) {
        newIndices.push(m.indexBuffer.ref.value.map(i => i + offset));
        offset += m.vertexCount;
    }
    const indices = concatArrays(Uint32Array, newIndices);
    return MS.Mesh.create(vertices, indices, normals, groups, nVertices, nTriangles);
}

/** Create Mesh from MeshListData */
export function makeMeshFromData(data: MeshlistData, meshIndex?: number, group?: number): MS.Mesh {
    if (meshIndex !== undefined) {
        const d = data.meshes[meshIndex];
        const nVertices = d.vertices.length;
        const nTriangles = d.triangles.length;
        const vertices = new Float32Array(d.vertices.flat());
        const indices = new Uint32Array(d.triangles.flat());
        const normals = new Float32Array(3 * nVertices);
        const groups = new Float32Array(nVertices).fill(group ?? 0);
        const mesh = MS.Mesh.create(vertices, indices, normals, groups, nVertices, nTriangles);
        MS.Mesh.computeNormals(mesh); // normals only necessary if flatShaded==false
        return mesh;
    } else {
        const meshes = data.meshes.map((m, i) => makeMeshFromData(data, i, group ?? m.mesh_id));
        return concat(...meshes);
    }
}

/** Example mesh - 1 triagle */
export function makeFakeMesh1(): MS.Mesh {
    const nVertices = 3;
    const nTriangles = 1;
    const vertices = new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0]);
    const indices = new Uint32Array([0, 1, 2]);
    const normals = new Float32Array([0, 0, 1]);
    const groups = new Float32Array([0]);
    return MS.Mesh.create(vertices, indices, normals, groups, nVertices, nTriangles);
}

/** Example mesh - irregular tetrahedron */
export function makeFakeMesh4(): MS.Mesh {
    const nVertices = 4;
    const nTriangles = 4;
    const vertices = new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]);
    const indices = new Uint32Array([0, 2, 1, 0, 1, 3, 1, 2, 3, 2, 0, 3]);
    const normals = new Float32Array([-1, -1, -1, 1, 0, 0, 0, 1, 0, 0, 0, 1]);
    const groups = new Float32Array([0, 1, 2, 3]);
    return MS.Mesh.create(vertices, indices, normals, groups, nVertices, nTriangles);
}

function sum(array: number[]): number {
    return array.reduce((a, b) => a + b, 0);
}

function concatArrays<T extends MS.TypedArray>(t: new (len: number) => T, arrays: T[]): T {
    const totalLength = arrays.map(a => a.length).reduce((a, b) => a + b, 0);
    const result: T = new t(totalLength);
    let offset = 0;
    for (const array of arrays) {
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
        const randId = Math.floor(Math.random() * curId);
        curId -= 1;
        // Swap it with the current element.
        const tmp = array[curId];
        array[curId] = array[randId];
        array[randId] = tmp;
    }
    return array;
}

