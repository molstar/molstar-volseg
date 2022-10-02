/** Helper functions for manipulation with mesh data. */

import * as MS from './molstar-lib-imports';


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

/** Return Mesh from CIF data and mesh IDs (group IDs). */
export function makeMeshFromCif(data: MS.CifFile, invertSides: boolean = true): [MS.Mesh, readonly number[]] {
    const volumeInfoBlock = data.blocks.find(b => b.header === 'VOLUME_INFO');
    const meshesBlock = data.blocks.find(b => b.header === 'MESHES');
    if (!volumeInfoBlock || !meshesBlock){
        throw new Error();
    }
    const meshCat = meshesBlock.categories['mesh'];
    const vertexCat = meshesBlock.categories['mesh_vertex'];
    const triangleCat = meshesBlock.categories['mesh_triangle'];
    if (!meshCat || !vertexCat || !triangleCat){
        throw new Error();
    }
    console.log('mesh cat', meshCat);
    console.log('vertex cat', vertexCat);
    console.log('triangle cat', triangleCat);
    const nVertices = vertexCat.rowCount;
    const nTriangles = Math.floor(triangleCat.rowCount / 3);
    const meshIds = meshCat.getField('id')!.toIntArray();
    const x = vertexCat.getField('x')!.toFloatArray();
    const y = vertexCat.getField('y')!.toFloatArray();
    const z = vertexCat.getField('z')!.toFloatArray();
    const vertices = flattenCoords(x, y, z);

    const groups_ = vertexCat.getField('mesh_id')!.toFloatArray()
    const starts = startMap(groups_);
    const triangleMeshIds = triangleCat.getField('mesh_id')!.toIntArray();
    const triangleVertexIds = triangleCat.getField('vertex_id')!.toIntArray();
    const indices_ = [];
    for (let i = 0; i < 3*nTriangles; i++){
        const offset = starts.get(triangleMeshIds[i])!;
        indices_.push(offset + triangleVertexIds[i]);
    }
    const indices = new Uint32Array(indices_);
    const groups = new Float32Array(groups_);
    const normals = new Float32Array(3 * nVertices);
    const mesh = MS.Mesh.create(vertices, indices, normals, groups, nVertices, nTriangles);
    MS.Mesh.computeNormals(mesh); // normals only necessary if flatShaded==false
    if (invertSides){
        modify(mesh, { invertSides: true }); // Vertex orientation convention is opposite in API and in MolStar
    }
    // TODO allow transform
    return [mesh, meshIds];
}

function flattenCoords(x: readonly number[], y: readonly number[], z: readonly number[]): Float32Array {
    const n = x.length;
    const out = new Float32Array(3 * n);
    for (let i = 0; i < x.length; i++) {
        out[3*i] = x[i];
        out[3*i+1] = y[i];
        out[3*i+2] = z[i];
    }
    return out;
}

/** Return bounding box */
export function bbox(mesh: MS.Mesh): MS.Box3D | null {  // Is there no function for this?
    const nVertices = mesh.vertexCount;
    const coords = mesh.vertexBuffer.ref.value;
    if (nVertices === 0) {
        return null;
    }
    let minX = coords[0], minY = coords[1], minZ = coords[2];
    let maxX = minX, maxY = minY, maxZ = minZ;
    for (let i = 0; i < 3*nVertices; i += 3){
        const x = coords[i], y = coords[i+1], z = coords[i+2];
        if (x < minX) minX = x;
        if (y < minY) minY = y;
        if (z < minZ) minZ = z;
        if (x > maxX) maxX = x;
        if (y > maxY) maxY = y;
        if (z > maxZ) maxZ = z;
    }
    return MS.Box3D.create(MS.Vec3.create(minX, minY, minZ), MS.Vec3.create(maxX, maxY, maxZ));
}

/** Get mappings of unique values to the position of their first occurrence */
export function startMap(values: readonly number[]){
    const result = new Map<number, number>();
    for (let i = 0; i < values.length; i++){
        if (!result.has(values[i])){
            result.set(values[i], i);
        }
    }
    return result;
}

/** Example mesh - 1 triangle */
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

