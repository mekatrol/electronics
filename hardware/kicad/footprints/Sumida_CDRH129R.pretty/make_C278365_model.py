"""Custom 3D model for Sumida CDRH129RNP-330MC / LCSC C278365.

Reference: Sumida CDRH129R, datasheet Ver.2024-07-29, pages 1-3:
https://products.sumida.com/products/pdf/CDRH129R_2024July.pdf

This is the 10uH-56uH geometry (33uH variant):
  nominal body 12 x 12 mm, 10 mm maximum height
  two underside terminals nominal 5.0 x 1.4 mm, along +/-Y
  recommended PCB land pattern: pads 5.7 x 2.6 mm,
    pad centres +/-5.2 mm from footprint origin.
  nominal mark '330' from earlier manufacturer part-specific datasheet.

Ferrite shield, drum core detail, edge breaks, metal wraps and marking are
visual approximations of the manufacturer's drawings/photos, NOT machining CAD.
The exposed terminal pads, footprint origin, and main envelope are based on
manufacturer dimensions.  Validate footprints before making a PCB.

Run: python make_C278365_model.py
Requires CadQuery / OCP.
"""
from pathlib import Path
import cadquery as cq

ROOT=Path(__file__).resolve().parent
NAME='C278365_Sumida_CDRH129RNP-330MC'

BODY=12.0
HEIGHT=9.75 # 10.0 mm maximum
TERMINAL_WIDTH=5.0 # 5.0 +/- 0.3 mm
TERMINAL_DEPTH=1.4 # 1.4 +/- 0.3 mm
TERMINAL_Y=5.25 # pad ranges 4.55..5.95, centres +/-5.25

SHIELD_COLOR=(0.115,0.126,0.141)
SHIELD_FACE=(0.16,0.17,0.183)
DRUM_COLOR=(0.20,0.207,0.218)
INK_COLOR=(0.63,0.66,0.69)
TERMINAL_COLOR=(0.69,0.68,0.63)
DARK_RECESS=(0.095,0.102,0.111)

# Octagonal (chamfered-square) ferrite shield. The drawing shows a 12mm
# square maximum envelope and diagonal cut-off corners.
h=BODY/2
corner=2.05
octagon=[(-h+corner,-h),(h-corner,-h),(h,-h+corner),
         (h,h-corner),(h-corner,h),(-h+corner,h),
         (-h,h-corner),(-h,-h+corner)]
shield=(cq.Workplane('XY').polyline(octagon).close()
        .extrude(9.18).translate((0,0,0.29)))
# Physical edges slightly softened to reveal shape in the 3D viewer.
shield=shield.edges('>Z').chamfer(0.17)
shield=shield.edges('<Z').chamfer(0.12)
# Circular well around ferrite drum, narrow gap visible around disk.
well=cq.Workplane('XY').circle(5.04).extrude(1.10).translate((0,0,8.50))
shield=shield.cut(well)
shield_solid=shield.val()

# Underlying shadow around the central cylinder, leaving a small seam.
recess_base=(cq.Workplane('XY').circle(4.95).extrude(.075)
             .translate((0,0,8.56)).val())
# Drum/core top sits just above the shield. Subtle roundover avoids the
# overly perfect sharp-cylinder look.
drum=(cq.Workplane('XY').circle(4.70).extrude(1.13)
      .translate((0,0,8.62)))
drum=drum.edges('>Z').fillet(.17)
drum=drum.edges('<Z').fillet(.09)
drum_solid=drum.val()  # top exactly 9.75mm

# Small circular mould impression on top, approximate physical feature seen
# in Sumida orthographic top view; it does NOT identify polarity or pin 1.
impression_x,impression_y=-2.70,-2.55
impression=(cq.Workplane('XY').center(impression_x,impression_y).circle(.27)
            .extrude(.035).translate((0,0,HEIGHT-.034)).val())
drum_solid=drum_solid.cut(impression)
recess_fill=(cq.Workplane('XY').center(impression_x,impression_y)
             .circle(.255).extrude(.006)
             .translate((0,0,HEIGHT-.033)).val())

# Plated/tinned leads on the underside, continuing up the package side.
# Datasheet underside electrode width 5.0+/-0.3 and 1.4+/-0.3 depth.
# Each terminal is a single contiguous solid. The vertical side wrap is an
# appearance approximation, kept in the same Y half as its underside pad.
def terminal(sign):
    underside=(cq.Workplane('XY')
               .box(TERMINAL_WIDTH,TERMINAL_DEPTH,.23,centered=(True,True,False))
               .translate((0,sign*TERMINAL_Y,0)))
    # Narrow side strip over the midpoint of the outer edge (y= +/-6).
    wrap=(cq.Workplane('XY').box(TERMINAL_WIDTH,.17,2.32,
                                centered=(True,True,False))
          .translate((0,sign*5.94,.09)))
    # Small metallic lip on upper side of strip.
    return underside.union(wrap).val()
term_negative=terminal(-1)
term_positive=terminal(1)

# Sumida earlier datasheet describes physical '330' stamp for 33uH variant.
# Printed on the face as very thin raised letters, to be visible in both
# STEP and VRML. Orientation reads upright when +Y points to image top.
marking=(cq.Workplane('XY',origin=(0,.12,HEIGHT-.001))
         .text('330',3.25,.010,font='Liberation Sans',kind='bold',
               halign='center',valign='center',combine=False))
marks=marking.solids().vals()

PARTS=[('Ferrite_shield',shield_solid,SHIELD_COLOR),
       ('Drum_base_shadow',recess_base,DARK_RECESS),
       ('Ferrite_drum_top',drum_solid,DRUM_COLOR),
       ('Mould_impression',recess_fill,SHIELD_COLOR),
       ('Terminal_1',term_negative,TERMINAL_COLOR),
       ('Terminal_2',term_positive,TERMINAL_COLOR)]
PARTS.extend((f'Stamp_330_{i}',s,INK_COLOR) for i,s in enumerate(marks,1))
for name,solid,_ in PARTS:
    assert solid.isValid(),name

ass=cq.Assembly(name=NAME)
for name,solid,rgb in PARTS:
    ass.add(solid,name=name,color=cq.Color(*rgb))
step=ROOT/(NAME+'.step')
ass.save(str(step),exportType='STEP')

# KiCad WRL coordinates are 1/2.54 of mm when imported with unity scaling.
# This matches the convention of the user's previous KiCad model packages.
wrl=['#VRML V2.0 utf8',
     '# Sumida CDRH129RNP-330MC / LCSC C278365',
     '# Dimensions: 12 x 12 x <=10 mm, terminal pitch 10.5mm',
     '# KiCad WRL coordinate convention: numeric mm / 2.54',
     'Group { children [']
for name,solid,rgb in PARTS:
    verts,triangles=solid.tessellate(tolerance=.08,angularTolerance=.24)
    if not triangles:continue
    metal=name.startswith('Terminal')
    wrl.extend([f'  # {name}','  Shape {','    appearance Appearance { material Material {',
                f'      diffuseColor {rgb[0]:.4f} {rgb[1]:.4f} {rgb[2]:.4f}',
                '      ambientIntensity 0.26',
                ('      specularColor 0.45 0.42 0.35' if metal else '      specularColor 0.07 0.07 0.07'),
                ('      shininess 0.44' if metal else '      shininess 0.12'),
                '    } }',
                '    geometry IndexedFaceSet {',
                '      solid TRUE','      creaseAngle 0.55',
                '      coord Coordinate { point ['])
    wrl.extend(f'        {p.x/2.54:.7f} {p.y/2.54:.7f} {p.z/2.54:.7f},' for p in verts)
    wrl.extend(['      ] }','      coordIndex ['])
    wrl.extend(f'        {a}, {b}, {c}, -1,' for a,b,c in triangles)
    wrl.extend(['      ]','    }','  }'])
wrl.extend([' ]','}',''])
vrml=ROOT/(NAME+'.wrl')
vrml.write_text('\n'.join(wrl),encoding='utf-8')

bbox=cq.Compound.makeCompound([s for _,s,_ in PARTS]).BoundingBox()
print('Files',step,vrml)
print('Extents mm X Y Z:',bbox.xlen,bbox.ylen,bbox.zlen)
print('Terminals centres mm X Y Z:',[(s.Center().x,s.Center().y,s.Center().z) for s in [term_negative,term_positive]])
print('Sizes bytes',step.stat().st_size,vrml.stat().st_size)
