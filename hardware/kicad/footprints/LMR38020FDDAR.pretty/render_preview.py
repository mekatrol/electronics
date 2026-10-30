"""Render CAD geometry with VTK; generate shareable annotated preview."""
from pathlib import Path
import vtk
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parent
ns={'__file__':str(root/'make_C5149193_model.py')}
exec((root/'make_C5149193_model.py').read_text(),ns)
solids=ns['solids']

R=vtk.vtkRenderer()
R.SetBackground(0.971,0.979,0.987)
win=vtk.vtkRenderWindow()
win.SetOffScreenRendering(1)
win.AddRenderer(R)
win.SetSize(1280,800)
win.SetMultiSamples(8)
for name,shape,rgb in solids:
    vv,ff=shape.tessellate(tolerance=.033,angularTolerance=.14)
    pts=vtk.vtkPoints()
    for v in vv: pts.InsertNextPoint(v.x,v.y,v.z)
    faces=vtk.vtkCellArray()
    for a,b,c in ff:
        faces.InsertNextCell(3)
        faces.InsertCellPoint(a)
        faces.InsertCellPoint(b)
        faces.InsertCellPoint(c)
    p=vtk.vtkPolyData();p.SetPoints(pts);p.SetPolys(faces)
    nf=vtk.vtkPolyDataNormals()
    nf.SetInputData(p);nf.SetSplitting(True);nf.SetFeatureAngle(43)
    nf.SetConsistency(True);nf.ComputeCellNormalsOn();nf.Update()
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(nf.GetOutputPort())
    actor=vtk.vtkActor();actor.SetMapper(mapper)
    prop=actor.GetProperty();prop.SetColor(*rgb);prop.SetAmbient(.32);prop.SetDiffuse(.70)
    metal=name.startswith('Lead_') or name=='Thermal_pad_9'
    prop.SetSpecular(.28 if metal else .07);prop.SetSpecularPower(24)
    R.AddActor(actor)

R.SetAutomaticLightCreation(True)
cam=R.GetActiveCamera()
cam.SetFocalPoint(0,0,.72)
cam.SetPosition(8.8,-9.6,11.4) # above upper left pin1 corner
cam.SetViewUp(0,0,1)
cam.ParallelProjectionOn();cam.SetParallelScale(4.4)
R.ResetCameraClippingRange()
win.Render()
writer=vtk.vtkPNGWriter();capture=vtk.vtkWindowToImageFilter()
capture.SetInput(win);capture.SetInputBufferTypeToRGB();capture.ReadFrontBufferOff();capture.Update()
raw=root/'_cad_render.png';writer.SetFileName(str(raw));writer.SetInputConnection(capture.GetOutputPort());writer.Write()
print(raw)

# Compose informative preview without confusing a modelled pin-1 dot with annotation.
W,H=1360,980
bg='#f6f8fa';canvas=Image.new('RGB',(W,H),bg)
draw=ImageDraw.Draw(canvas)
fbase='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';fbold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
head=ImageFont.truetype(fbold,40)
sub=ImageFont.truetype(fbase,23)
small=ImageFont.truetype(fbase,19)
draw.text((65,36),'Texas Instruments  LMR38020FDDAR',font=head,fill='#1d2a34')
draw.text((67,93),'LCSC C5149193  |  DDA0008B  |  HSOIC-8 PowerPAD',font=sub,fill='#56616d')
model=Image.open(raw).convert('RGB')
# Fit raw CAD render inside ample page space
model=model.resize((1280,800),Image.Resampling.LANCZOS)
canvas.paste(model,(40,127))
draw.text((70,923),'Top marking: C3802F   •   Pin 1: small recessed dot   •   Exposed pad on underside',font=small,fill='#4d5f6b')
canvas.save(root/(ns['NAME']+'_preview.png'),optimize=True)
print('preview saved')
