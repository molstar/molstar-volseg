from pathlib import Path
import numpy as np
from vtk import vtkSphereSource, vtkPolyData, vtkDecimatePro, vtkIdList, vtkPoints, vtkFloatArray, vtkCellArray
from vtkmodules.util.numpy_support import vtk_to_numpy

# create mesh
def mkVtkIdList(it):
  vil = vtkIdList()
  for i in it:
    vil.InsertNextId(int(i))
  return vil

def CreateMesh(modelNode, arrayVertices, arrayTriangles):
  # modelNode : a vtkMRMLModelNode in the Slicer scene which will hold the mesh
  # arrayVertices : list of triples [[x1,y1,z2], [x2,y2,z2], ... ,[xn,yn,zn]] of vertex coordinates
  # arrayVertexNormals : list of triples [[nx1,ny1,nz2], [nx2,ny2,nz2], ... ] of vertex normals
  # arrayTriangles : list of triples of 0-based indices defining triangles
  # labelsScalars : list of strings such as ["bipolar", "unipolar"] to label the individual scalars data sets
  # arrayScalars : an array of n rows for n vertices and m colums for m inidividual scalar sets

  # create the building blocks of polydata including data attributes.
  mesh    = vtkPolyData()
  points  = vtkPoints()
#   normals = vtkFloatArray()
  polys   = vtkCellArray()
  
  # load the array data into the respective VTK data structures
  for i in range(len(arrayVertices)):
    points.InsertPoint(i, arrayVertices[i])
  
  for i in range(len(arrayTriangles)):
    polys.InsertNextCell(mkVtkIdList(arrayTriangles[i]))
  
#   for i in range(len(arrayVertexNormals)):
#     normals.InsertTuple3(i, arrayVertexNormals[i][0], arrayVertexNormals[i][1], arrayVertexNormals[i][2])
  
  # put together the mesh object
  mesh.SetPoints(points)
  mesh.SetPolys(polys)
#   if(len(arrayVertexNormals) == len(arrayVertices)):
#     mesh.GetPointData().SetNormals(normals)
  
  # Add scalars
  
  modelNode.SetAndObservePolyData(mesh)


def decimation(inputPoly: vtkPolyData):
    sphereS = vtkSphereSource()
    sphereS.Update()

    # inputPoly = vtkPolyData()
    
    # inputPoly.ShallowCopy(sphereS.GetOutput())

    print("Before decimation\n"
          "-----------------\n"
          "There are " + str(inputPoly.GetNumberOfPoints()) + "points.\n"
          "There are " + str(inputPoly.GetNumberOfPolys()) + "polygons.\n")

    decimate = vtkDecimatePro()
    decimate.SetInputData(inputPoly)
    decimate.SetTargetReduction(.10)
    decimate.Update()

    decimatedPoly = vtkPolyData()
    decimatedPoly.ShallowCopy(decimate.GetOutput())

    print("After decimation \n"
          "-----------------\n"
          "There are " + str(decimatedPoly.GetNumberOfPoints()) + "points.\n"
          "There are " + str(decimatedPoly.GetNumberOfPolys()) + "polygons.\n")


def create_mesh_from_vertices_and_triangles(triangles: np.ndarray, vertices: np.ndarray):
    mesh    = vtkPolyData()
    points  = vtkPoints()
#   normals = vtkFloatArray()
    polys   = vtkCellArray()
    
    for i in range(len(vertices)):
        points.InsertPoint(i, vertices[i])
    
    for i in range(len(triangles)):
        polys.InsertNextCell(mkVtkIdList(triangles[i]))
    
    
    mesh.SetPoints(points)
    mesh.SetPolys(polys)
    return mesh

def get_vertices_and_triangles_from_vtk_mesh(mesh: vtkPolyData):
    triangles: vtkCellArray = mesh.GetPolys()
    vertices: vtkPoints = mesh.GetPoints()
    # TODO: convert to np arrs
    # https://discourse.vtk.org/t/convert-vtk-array-to-numpy-array/3152
    # numpy_interface
    # print(len(triangles), len(vertices))
    return (vtk_to_numpy(triangles), vtk_to_numpy(vertices))

def decimate_mesh(mesh: vtkPolyData, fraction: float):
    assert fraction <= 1.0
  # TODO: quadratic?
    decimate = vtkDecimatePro()
    decimate.SetInputData(mesh)
    decimate.SetTargetReduction(fraction)
    decimate.Update()

    decimatedPoly = vtkPolyData()
    decimatedPoly.ShallowCopy(decimate.GetOutput())
    return decimatedPoly
