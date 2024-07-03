import numpy as np
import pymeshlab as ml


def convert_mesh_to_pymeshlab(vertices: np.ndarray, triangles: np.ndarray):
    mesh = ml.Mesh(face_matrix=triangles, edge_matrix=vertices)
    ms = ml.MeshSet()
    ms.add_mesh()
    m = ms.current_mesh()
    print("input mesh has", m.vertex_number(), "vertex and", m.face_number(), "faces")
    return ms


def downsample_pymeshlab_mesh(ms: ml.MeshSet, fraction: float):
    # TODO: use pymeshlab, compute target based on provided fraction
    ms = ml.MeshSet()
    ms.load_new_mesh("input.ply")
    m = ms.current_mesh()
    print("input mesh has", m.vertex_number(), "vertex and", m.face_number(), "faces")

    # Target number of vertex
    TARGET: float = ms.current_mesh().vertex_number() * fraction

    # Estimate number of faces to have 100+10000 vertex using Euler
    numFaces = 100 + 2 * TARGET

    # Simplify the mesh. Only first simplification will be agressive
    while ms.current_mesh().vertex_number() > TARGET:
        ms.apply_filter(
            "simplification_quadric_edge_collapse_decimation",
            targetfacenum=numFaces,
            preservenormal=True,
        )
        print(
            "Decimated to",
            numFaces,
            "faces mesh has",
            ms.current_mesh().vertex_number(),
            "vertex",
        )
        # Refine our estimation to slowly converge to TARGET vertex number
        numFaces = numFaces - (ms.current_mesh().vertex_number() - TARGET)

    m = ms.current_mesh()
    print("output mesh has", m.vertex_number(), "vertex and", m.face_number(), "faces")
    # ms.save_current_mesh('output.ply')
    return ms


def get_vertices_and_triangles_from_pymeshlab_mesh(ms: ml.MeshSet):
    vertices = ms.current_mesh().vertex_number()
    triangles = ms.current_mesh().face_number()
    return vertices, triangles
