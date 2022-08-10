import { Metadata, MeshData } from "./data";


export interface IVolumeServerClient {
    /** Run an asynchronous request to API to get metadata for a given entry.
     * e.g. 
     * ```
     * const metadata = await client.getMetadata('empiar', 'empiar-10070');
     * ```
     */
    getMetadata(source: string, entryId: string): Promise<Metadata[]>;
    
    /** Run an asynchronous request to API to get meshes for a given segment in a given entry at given detail level.
     * e.g. 
     * ```
     * const meshes = await client.getMeshes('empiar', 'empiar-10070', 1, 7);
     * ```
     */
    getMeshes(source: string, entryId: string, segmentId: number, detail: number): Promise<MeshData[]>;
    
    /** Run an asynchronous request to API to get meshes for a given segment in a given entry at given detail level.
     * Include only the triangles that have at least one vertex within the given box.
     * e.g. 
     * ```
     * const meshes = await client.getMeshesWithinBox('empiar', 'empiar-10070', 1, 7, [[-1000, -1000, -1000], [1000, 1000, 1000]]);
     * ```
     */
    getMeshesWithinBox(source: string, entryId: string, segmentId: number, detail: number, box: [[number, number, number], [number, number, number]]): Promise<MeshData[]>;

    // TODO add methods for density data (box, cell)
}
