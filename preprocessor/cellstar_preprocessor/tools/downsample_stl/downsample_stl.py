import shutil
from pathlib import Path

import pymeshlab as ml


def downsample_stl(input: Path, output: Path, rate: float):
    if output.exists():
        if output.is_file():
            output.unlink()
        else:
            shutil.rmtree(output)

    ms = ml.MeshSet()
    ms.load_new_mesh(str(input.resolve()))
    m = ms.current_mesh()
    print("input mesh has", m.vertex_number(), "vertex and", m.face_number(), "faces")

    # Target number of vertex
    TARGET = int(ms.current_mesh().vertex_number() * rate)

    # Estimate number of faces to have 100+10000 vertex using Euler
    numFaces = 100 + 2 * TARGET

    # Simplify the mesh. Only first simplification will be agressive
    # TODO: for list of filters MeshSet.print_filter_list function
    while ms.current_mesh().vertex_number() > TARGET:
        ms.apply_filter(
            # TODO: try other filters?
            # "simplification_edge_collapse_for_marching_cube_meshes",
            # "simplification_quadric_edge_collapse_decimation",
            "meshing_decimation_quadric_edge_collapse",
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
    ms.save_current_mesh(str(output.resolve()))
