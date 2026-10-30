"""Export two accurate CAD renders and labelled one-page PNG preview."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import vtk
ROOT=Path(__file__).resolve().parent
ns={'__file__':str(ROOT/'make_C278365_model.py')}
exec((ROOT/'make_C278365_model.py').read_text(),ns)
PARTS=ns['PARTS']

def cad_view(path, camera, up, scale, size=(1250,850)):
    r=vtk.vtkRenderer()
    r.SetBackground(0.978,0.983,0.989)
    w=vtk.vtkRenderWindow();w.SetOffScreenRendering(1);w.AddRenderer(r);w.SetSize(*size);w.SetMultiSamples(8)
    for name,shape,color in PARTS:
        vertices,tri=shape.tessellate(tolerance=.075,angularTolerance=.20)
        vp=vtk.vtkPoints()
        for v in vertices:vp.InsertNextPoint(v.x,v.y,v.z)
        f=vtk.vtkCellArray()
        for a,b,c in tri:
            f.InsertNextCell(3)
            f.InsertCellPoint(a);f.InsertCellPoint(b);f.InsertCellPoint(c)
        p=vtk.vtkPolyData();p.SetPoints(vp);p.SetPolys(f)
        normals=vtk.vtkPolyDataNormals();normals.SetInputData(p);normals.SetConsistency(True)
        normals.SetSplitting(True);normals.SetFeatureAngle(49);normals.Update()
        m=vtk.vtkPolyDataMapper();m.SetInputConnection(normals.GetOutputPort())
        act=vtk.vtkActor();act.SetMapper(m)
        prop=act.GetProperty();prop.SetColor(*color)
        prop.SetAmbient(.31);prop.SetDiffuse(.71)
        metallic=name.startswith('Terminal_')
        prop.SetSpecular(.26 if metallic else .075);prop.SetSpecularPower(26 if metallic else 17)
        r.AddActor(act)
    r.SetAutomaticLightCreation(True)
    c=r.GetActiveCamera();c.SetFocalPoint(0,0,4.6);c.SetPosition(*camera)
    c.SetViewUp(*up);c.ParallelProjectionOn();c.SetParallelScale(scale)
    r.ResetCameraClippingRange();w.Render()
    save=vtk.vtkPNGWriter();f=vtk.vtkWindowToImageFilter();f.SetInput(w)
    f.SetInputBufferTypeToRGB();f.ReadFrontBufferOff();f.Update()
    save.SetInputConnection(f.GetOutputPort());save.SetFileName(str(path));save.Write()

cad_view(ROOT/'_top_iso.png',(21,-24,25),(0,0,1),11.9)
cad_view(ROOT/'_underside.png',(13,-17,-23),(0,0,1),12.5)

WIDTH,HEIGHT=1400,1060
canvas=Image.new('RGB',(WIDTH,HEIGHT),'#f6f8fb')
draw=ImageDraw.Draw(canvas)
regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
f_title=ImageFont.truetype(bold,38)
f_sub=ImageFont.truetype(regular,23)
f_section=ImageFont.truetype(bold,22)
f_note=ImageFont.truetype(regular,20)
draw.text((60,35),'Sumida  CDRH129RNP-330MC',font=f_title,fill='#182b3b')
draw.text((61,91),'LCSC C278365  |  33 µH shielded SMD power inductor',font=f_sub,fill='#607182')
main=Image.open(ROOT/'_top_iso.png').convert('RGB')
# Crop background empty edges and resize to main card rectangle
main=main.resize((1270,860),Image.Resampling.LANCZOS)
canvas.paste(main,(45,130))
# Compact underside view to make the terminal orientation unambiguous.
inset=Image.open(ROOT/'_underside.png').convert('RGB')
inset=inset.resize((365,249),Image.Resampling.LANCZOS)
draw.rounded_rectangle((970,170,1353,487),radius=14,fill='#eef2f6',outline='#d7dfe8',width=2)
draw.text((990,184),'Underside / terminals',font=f_section,fill='#263b4b')
canvas.paste(inset,(980,224))
# lower right label not overlap model: text across bottom strip
draw.rounded_rectangle((60,936,1338,1030),radius=14,fill='#e7edf3')
draw.text((85,955),'Top stamp: 330   |   Nominal body: 12 × 12 mm   |   Height: ≤ 10 mm',font=f_note,fill='#354657')
draw.text((85,990),'Two terminal pads underneath, centred at Y = ±5.25 mm',font=f_note,fill='#354657')
preview=ROOT/(ns['NAME']+'_preview.png')
canvas.save(preview,optimize=True)
print('PREVIEW:',preview)
