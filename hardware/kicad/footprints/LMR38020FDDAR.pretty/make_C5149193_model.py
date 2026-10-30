"""KiCad 10 3D model for TI LMR38020FDDAR / LCSC C5149193.

Reference: Texas Instruments LMR38020, SNVSC40E (rev E), package drawing
DDA0008B (4214849/B, 09/2025), pp.37-38 of current PDF, and package marking
C3802F listed in packaging addendum.
https://www.ti.com/lit/ds/symlink/lmr38020.pdf

All CAD dimensions are millimetres, envelope and lead position nominal.
The mould edge radii, gull-wing bending detail, laser print and pin-1 dot are
VISUAL approximations; check pin orientation against the KiCad footprint.

CadQuery (with OCP) required to regenerate STEP and VRML.
"""
import math
from pathlib import Path
import cadquery as cq
OUT=Path(__file__).resolve().parent
NAME='C5149193_TI_LMR38020FDDAR'

# Dimensions in millimetres, using package drawing DDA0008B
BODY_X=3.90
BODY_Y=4.90
BODY_BOTTOM=0.18
TOP_Z=1.65 # under package max 1.70 mm
LEAD_EXTENT_X=3.10  # overall 6.2 max, nominal 6.0; lead tips at +/- 3.00
LEAD_THICK=0.16
LEAD_WIDTH=0.41
PITCH=1.27
PAD_X=2.41 # thermal pad nominal from 2.11 to 2.71
PAD_Y=3.10 # thermal pad nominal from 2.8 to 3.4

BLACK=(0.106,0.117,0.133)
SILVER=(0.70,0.75,0.78)
ETCH=(0.69,0.74,0.74)
DOT_COLOR=(0.36,0.39,0.41)

# Black epoxy moulded package with soft machined / cast edges
body=(cq.Workplane('XY').box(BODY_X,BODY_Y,TOP_Z-BODY_BOTTOM, centered=(True,True,False))
      .translate((0,0,BODY_BOTTOM)).edges('|Z').fillet(0.065)
      .edges('>Z').fillet(0.07).val())

# Pin 1: upper-left corner with text correctly readable from above. A lightly
# recessed dot is built into the solid, rather than ink alone, to remain
# visible in a STEP-only KiCad display. Dot diameter/depth are illustrative.
DOT_X,DOT_Y=-1.42,1.87
DOT_R=0.145
DOT_DEPTH=.055
pocket=(cq.Workplane('XY').center(DOT_X,DOT_Y)
        .circle(DOT_R).extrude(DOT_DEPTH+.012)
        .translate((0,0,TOP_Z-DOT_DEPTH)).val())
body=body.cut(pocket)

# Tin-plated exposed thermal pad (bottom side). Its top meets the resin body.
thermal=(cq.Workplane('XY').box(PAD_X,PAD_Y,BODY_BOTTOM,centered=(True,True,False))
         .edges('|Z').fillet(.045).val())

# Eight sheet-metal gull-wing terminals. The side-profile is approximated
# using a series of bend facets; tip width is within stated 5.8-6.2 mm span.
# Profiles in world (x,z); Y extrusion makes 0.41-mm wide terminal fingers.
lead_profile=[
 (1.88, .91),
 (2.025,.91),
 (2.12,.84),
 (2.205,.54),
 (2.31,.27),
 (2.43,.175),
 (3.00,.16),
 (3.00,0.00),
 (2.41,0.012),
 (2.23,.11),
 (2.14,.28),
 (2.04,.63),
 (1.975,.75),
 (1.88,.75),
]

def lead(x_sign, y_center):
    section=[(x*x_sign,z) for x,z in lead_profile]
    if x_sign<0:
        section.reverse()
    return (cq.Workplane('XZ').polyline(section).close().extrude(LEAD_WIDTH)
            .translate((0,y_center+LEAD_WIDTH/2,0)).val())

# Standard package top view, positive Y up, printing reads left to right:
# 1 8 at top; 4 5 at bottom. See TI datasheet section 6.
leads=[]
for i in range(4):
    y=(1.5-i)*PITCH
    leads.append((i+1,lead(-1,y)))
    leads.append((8-i,lead(+1,y)))
leads=sorted(leads)

# Bottom of recessed dot is coloured dark-grey to keep the subtle locating mark
# visible from KiCad's 3D viewer; separate thin face is not a raised bump.
dot_base=(cq.Workplane('XY').center(DOT_X,DOT_Y)
          .circle(DOT_R-.01).extrude(.003)
          .translate((0,0,TOP_Z-DOT_DEPTH+.001)).val())

# Real manufacturer's marking for this orderable part is 'C3802F'.  The
# printed font height is an approximation, kept below package height tolerance.
text_solids=(cq.Workplane('XY',origin=(0.14,-0.13,TOP_Z-.002))
             .text('C3802F',0.73,.006,font='Liberation Sans',kind='regular',
                   halign='center',valign='center',combine=False).solids().vals())

solids=[('Epoxy_package',body,BLACK),('Thermal_pad_9',thermal,SILVER)]
solids.extend((f'Lead_{i}',s,SILVER) for i,s in leads)
solids.append(('Pin1_recess_shading',dot_base,DOT_COLOR))
solids.extend((f'Marking_{i+1}',s,ETCH) for i,s in enumerate(text_solids))

for name,solid,_ in solids:
    if not solid.isValid():
        raise ValueError(f'Invalid 3D solid: {name}')

assy=cq.Assembly(name=NAME)
for name,s,rgb in solids:
    assy.add(s,name=name,color=cq.Color(*rgb))
stepfile=OUT/(NAME+'.step')
assy.save(str(stepfile),exportType='STEP')

# VRML2 models use coordinates in inches; KiCad scales by 2.54 cm/in and
# interprets WRL model as 0.1-inch units. The existing tested models in this
# project use numeric millimetre / 2.54 coordinates, so repeat that scheme.
wrl=['#VRML V2.0 utf8',
     '# Texas Instruments LMR38020FDDAR  LCSC C5149193',
     '# DDA0008B SO PowerPAD 8 - 4.90x3.90 body, 1.27 pitch',
     '# Mesh vertex coordinates = physical mm / 2.54 (KiCad VRML)',
     'Group { children [']
for name,solid,rgb in solids:
    verts,triangles=solid.tessellate(tolerance=.027,angularTolerance=.18)
    if not triangles: continue
    metallic=name.startswith('Lead_') or name=='Thermal_pad_9'
    wrl.extend([
        f'  # {name}',
        '  Shape {',
        '    appearance Appearance { material Material {',
        f'      diffuseColor {rgb[0]:.4f} {rgb[1]:.4f} {rgb[2]:.4f}',
        '      ambientIntensity 0.24',
        '      specularColor '+('0.40 0.40 0.40' if metallic else '0.07 0.07 0.07'),
        '      shininess '+('0.46' if metallic else '0.11'),
        '    } }',
        '    geometry IndexedFaceSet {',
        '      solid TRUE',
        '      creaseAngle 0.68',
        '      coord Coordinate { point ['])
    wrl.extend(f'        {p.x/2.54:.8f} {p.y/2.54:.8f} {p.z/2.54:.8f},' for p in verts)
    wrl.extend(['      ] }','      coordIndex ['])
    wrl.extend(f'        {a}, {b}, {c}, -1,' for a,b,c in triangles)
    wrl.extend(['      ]','    }','  }'])
wrl.extend([' ]','}',''])
wrlfile=OUT/(NAME+'.wrl')
wrlfile.write_text('\n'.join(wrl),encoding='utf-8')

# Geometric check (ignoring tiny top ink thickness): lead X span should 6mm,
# Y body length 4.9mm, and top no greater than 1.70mm.
shapes=[s for _,s,_ in solids]
from OCP.BRepBndLib import BRepBndLib
BB=cq.Compound.makeCompound(shapes).BoundingBox()
print('STEP:',stepfile,'size',stepfile.stat().st_size)
print('WRL:',wrlfile,'size',wrlfile.stat().st_size)
print('CAD extents (mm):',BB.xlen,BB.ylen,BB.zlen)
print('Pad centres: '+', '.join(f'{i} @ ({s.Center().x:+.2f}, {s.Center().y:+.2f})' for i,s in leads))
print('Body:',BODY_X,BODY_Y,'Z:',TOP_Z,'thermal:',PAD_X,PAD_Y)
