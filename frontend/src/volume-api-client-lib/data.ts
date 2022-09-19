
// METADATA

export interface Metadata {
    grid: { 
        general: { 
            details: string ,
        },
        volumes: Volumes,
        segmentation_lattices: SegmentationLattices,
        segmentation_meshes: SegmentationMeshes,
    },
    annotation: Annotation,
}

export interface Volumes {
    volume_downsamplings: number[],
    voxel_size: { [downsampling: number]: Vector3 },
    origin: Vector3,
    grid_dimensions: Vector3,
    sampled_grid_dimensions: { [downsampling: number]: Vector3 },
    mean: { [downsampling: number]: string }, // this should be encoded as number, IMHO
    std: { [downsampling: number]: string }, // this should be encoded as number, IMHO
    min: { [downsampling: number]: string }, // this should be encoded as number, IMHO
    max: { [downsampling: number]: string }, // this should be encoded as number, IMHO
    volume_force_dtype: string,
}

export interface SegmentationLattices {
    segmentation_lattice_ids: number[],
    segmentation_downsamplings: { [lattice: number]: number[] },
}

export interface SegmentationMeshes {
    mesh_component_numbers: {
        segment_ids: {
            [segId: number]: {
                detail_lvls: {
                    [detail: number]: {
                        mesh_ids: {
                            [meshId: number]: {
                                num_triangles: number,
                                num_vertices: number
                            }
                        }
                    }
                }
            }
        }
    }
    detail_lvl_to_fraction: { 
        [lvl: number]: number 
    }
}

export interface Annotation {
    name: string,
    details: string,
    segment_list: Segment[],
}

export interface Segment {
    id: number,
    colour: number[],
    biological_annotation: BiologicalAnnotation,
}

export interface BiologicalAnnotation {
    name: string,
    external_references: { id: number, resource: string, accession: string, label: string, description: string }[]
}

type Vector3 = [number, number, number];


// MESH DATA

/** Data representing a single mesh */
export interface MeshData {
    /** Unique numeric identifier of a mesh within a segment 
     * (Actually I don't have any real-life example of a segment that would contain more than one mesh.
     * Maybe Aliaksei will know.) */
    mesh_id: number,
    
    /** Array of vertex indices [A0, B0, C0, A1, B1, C1, ... A(m-1), B(m-1), C(m-1)], 
     * where m is the number of triangles, 
     * and i-th triangle is formed by vertices Ai, Bi, Ci */
    triangles: number[],
    
    /** Array of floats [x0, y0, z0, x1, y1, z1, ... x(n-1), y(n-1), z(n-1)], 
     * where n is the number of vertices, 
     * and j-th vertex has coordinates xj, yj, zj */ 
    vertices: number[],  
}



