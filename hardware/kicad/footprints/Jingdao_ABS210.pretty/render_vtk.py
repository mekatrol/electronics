"""Render a CAD inspection preview from the actual STEP geometry using VTK."""
from pathlib import Path
import cadquery as cq
from OCP.STEPControl import STEPControl_Reader
import vtk
from PIL import Image, ImageDraw, ImageFont
from vtk.util.numpy_support import numpy_to_vtk
import numpy as np

# Get original assembly with material colors by rerunning shape script? avoid dynamic import
# Instead for rendering load color-separated geometry from CadQuery assembly via STEP CAF.
# Uncolored output from STEP reader -> easiest to rely on original source in exec globals.
exec((Path(__file__).parent/'make_C123897_model.py').read_text().split('# 3D preview with 3/4 angle')[0])
renderer=vtk.vtkRenderer()
renderer.SetBackground(0.972,0.978,0.987)
win=vtk.vtkRenderWindow()
win.SetOffScreenRendering(1)
win.AddRenderer(renderer)
win.SetSize(1300,860)
win.SetMultiSamples(8)
for name,shape,rgb in solids:
    verts,faces=shape.tessellate(tolerance=.028,angularTolerance=.12)
    points=vtk.vtkPoints()
    points.SetNumberOfPoints(len(verts))
    for i,pt in enumerate(verts):
        points.SetPoint(i,pt.x,pt.y,pt.z)
    cellarray=vtk.vtkCellArray()
    for a,b,c in faces:
        cellarray.InsertNextCell(3)
        cellarray.InsertCellPoint(a)
        cellarray.InsertCellPoint(b)
        cellarray.InsertCellPoint(c)
    pd=vtk.vtkPolyData()
    pd.SetPoints(points)
    pd.SetPolys(cellarray)
    # Normals for surface lighting. No vertex blending across edges.
    nf=vtk.vtkPolyDataNormals()
    nf.SetInputData(pd)
    nf.SetSplitting(True)
    nf.SetFeatureAngle(35)
    nf.SetConsistency(True)
    nf.ComputeCellNormalsOn()
    nf.Update()
    mapper=vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(nf.GetOutputPort())
    actor=vtk.vtkActor(); actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*rgb)
    actor.GetProperty().SetAmbient(.28)
    actor.GetProperty().SetDiffuse(.74)
    actor.GetProperty().SetSpecular(.12 if name.startswith('Lead') else .06)
    actor.GetProperty().SetSpecularPower(25)
    renderer.AddActor(actor)
renderer.SetAutomaticLightCreation(True)
cam=renderer.GetActiveCamera()
cam.SetFocalPoint(0,0,.57)
cam.SetPosition(-9,-10,10)
cam.SetViewUp(0,0,1)
cam.ParallelProjectionOn()
cam.SetParallelScale(4.55)
renderer.ResetCameraClippingRange()
win.Render()
filter=vtk.vtkWindowToImageFilter()
filter.SetInput(win)
filter.SetInputBufferTypeToRGB()
filter.ReadFrontBufferOff()
filter.Update()
writer=vtk.vtkPNGWriter()
out=Path(__file__).parent/'_vtk_render.png'
writer.SetFileName(str(out))
writer.SetInputConnection(filter.GetOutputPort())
writer.Write()
print('wrote',out)
