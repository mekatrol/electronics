"""C123897 / Jingdao Microelectronics ABS210, KiCad STEP and coloured VRML.

Mechanical source: Jingdao ABS201--ABS210 datasheet, page 3:
https://www.lcsc.com/datasheet/C123897.pdf

Units: millimetres. Nominal envelope: 6.2 (lead tips X) x 5.05
(body in Y) x 1.40 high. Body width X = 4.35. Four nominal lead
centres are (X=+/-2.975, Y=+/-2.0). The radius, lead bends, top stamp
size and ink depth are VISUAL approximations (not individually specified).

The x/y orientation of the four numbered pads is footprint-dependent.
Make sure KiCad's 3D preview aligns leads and polarity orientation
with your particular footprint before committing to a PCB layout.

CadQuery >= 2.3 needed to regenerate; matplotlib needed for PNG preview.
"""
from pathlib import Path
import math
import cadquery as cq

OUT = Path(__file__).resolve().parent
BASE = 'C123897_Jingdao_ABS210'
BODY_W, BODY_L = 4.35, 5.05
TOTAL_W, Z_TOP = 6.2, 1.40
BODY_Z0 = 0.20
TERMINAL_W = 0.60
LEAD_Y = 2.0
NOMINAL_PAD_X = 2.975

# Appearance choices reflect plastic / matte-tin / light-grey laser marking.
BODY_RGB = (0.110, 0.123, 0.139)
LEAD_RGB = (0.71, 0.74, 0.76)
MARK_RGB = (0.72, 0.74, 0.71)
NOTCH_RGB = (0.082, 0.09, 0.102)

# Moulded housing. Top edge is softened; body and total height are nominal.
body = (cq.Workplane('XY')
        .box(BODY_W, BODY_L, Z_TOP-BODY_Z0, centered=(True,True,False))
        .translate((0,0,BODY_Z0))
        .edges().fillet(0.075))
# Semicircular package-indexing recess at left edge of top view.
# Increased modestly from the earlier shallow 0.43 x 0.06 mm pocket,
# which became nearly invisible in KiCad's typical 3D viewer angles.
# Still an appearance approximation: the manufacturer gives no dimensions.
NOTCH_RADIUS = 0.56
NOTCH_DEPTH = 0.18
notch = (cq.Workplane('XY').center(-BODY_W/2, 0)
         .circle(NOTCH_RADIUS).extrude(NOTCH_DEPTH)
         .translate((0,0,Z_TOP-NOTCH_DEPTH)))
body = body.cut(notch).val()

# A lead is a bent, constant-width sheet of ~0.20 mm, with planar feet.
# The source drawing specifies widths/heights but not each bend radius,
# so a side profile is traced with several points for a realistic silhouette.
# Profile is expressed in XY workplane where sketch X -> world X, sketch Y -> world Z.
# The extrude direction is world -Y, then translate to desired lead centre.
lead_profile = [
    (2.035, 0.99),  # encapsulated inner section
    (2.240, 0.99),
    (2.360, 0.91),
    (2.490, 0.42),
    (2.615, 0.23),
    (2.720, 0.18),
    (3.100, 0.18),
    (3.100, 0.00),
    (2.652, 0.00),
    (2.475, 0.105),
    (2.338, 0.33),
    (2.192, 0.80),
    (2.035, 0.80),
]

def make_lead(xsign,ycenter):
    # CQ XZ workplane normal points to -Y. Extrude and translate place y span.
    profile = [(xsign*x,z) for x,z in lead_profile]
    if xsign < 0:
        profile = list(reversed(profile))
    sh = (cq.Workplane('XZ')
          .polyline(profile).close().extrude(TERMINAL_W)
          .translate((0, ycenter + TERMINAL_W/2, 0)).val())
    if not sh.isValid():
        raise RuntimeError('Bad extruded lead')
    return sh

# Map points in top view: 1 right bottom, 2 right top, 3 left top, 4 left bottom;
# users must verify against the numbering on THEIR KiCad footprint.
leads = [(1, make_lead(+1,-LEAD_Y)),
         (2, make_lead(+1,+LEAD_Y)),
         (3, make_lead(-1,+LEAD_Y)),
         (4, make_lead(-1,-LEAD_Y))]

# Slightly raised pale print makes the marking visible in both STEP and VRML.
# Horizontal text (readable left-to-right in standard XY view) deliberately
# avoids the upside-down marking issue encountered with the earlier fuse.
markings = []
for row_idx, (text, font_size, xy) in enumerate([
    ('ABS210', 0.70, (0.05, -0.33)),
]):
    wp = (cq.Workplane('XY',origin=(xy[0],xy[1],Z_TOP-0.001))
          .text(text, font_size, .009, font='Liberation Sans', kind='regular',
                halign='center', valign='center', combine=False))
    markings.extend(wp.solids().vals())

solids = [('Moulded_case',body,BODY_RGB)]
solids += [(f'Lead_{i}', sh, LEAD_RGB) for i,sh in leads]
solids += [(f'Ink_{i+1}', sh, MARK_RGB) for i,sh in enumerate(markings)]

for name, solid, _ in solids:
    if not solid.isValid():
        raise ValueError(f'Invalid solid {name}')

assy = cq.Assembly(name='C123897_Jingdao_ABS210')
for name,shape,rgb in solids:
    assy.add(shape, name=name, color=cq.Color(*rgb))
step_path = OUT / (BASE+'.step')
assy.save(str(step_path), exportType='STEP')

# Coloured VRML2, with KiCad VRML model unit = 2.54 mm. Independent
# meshes/materials preserve matte metallic leads and light printed text.
lines = ['#VRML V2.0 utf8',
         '# Jingdao Microelectronics ABS210, LCSC C123897',
         '# Vertices mm / 2.54 for KiCad VRML convention',
         '# Body 4.35 x 5.05 mm; lead tip span 6.20 mm; max height 1.40 mm',
         'Group { children [']
for name,solid,rgb in solids:
    verts,tris = solid.tessellate(tolerance=0.035, angularTolerance=0.20)
    if not tris:
        continue
    lines += [
        f'  # {name}',
        '  Shape {',
        '    appearance Appearance { material Material {',
        f'      diffuseColor {rgb[0]:.4f} {rgb[1]:.4f} {rgb[2]:.4f}',
        '      ambientIntensity 0.27',
        '      specularColor '+ ('0.36 0.36 0.36' if name.startswith('Lead_') else '0.06 0.06 0.06'),
        '      shininess '+('0.38' if name.startswith('Lead_') else '0.12'),
        '    } }',
        '    geometry IndexedFaceSet {',
        '      solid TRUE',
        '      creaseAngle 0.70',
        '      coord Coordinate { point [',
    ]
    lines.extend(f'        {p.x/2.54:.7f} {p.y/2.54:.7f} {p.z/2.54:.7f},' for p in verts)
    lines.extend(['      ] }','      coordIndex ['])
    lines.extend(f'        {a}, {b}, {c}, -1,' for a,b,c in tris)
    lines.extend(['      ]','    }','  }'])
lines.extend([' ]','}',''])
wrl_path=OUT/(BASE+'.wrl')
wrl_path.write_text('\n'.join(lines), encoding='utf-8')

# 3D preview with 3/4 angle, and labelled pin-location illustration.
try:
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(10.7,6.8), dpi=160, facecolor='#f3f6f8')
    ax=fig.add_subplot(111, projection='3d', computed_zorder=False)
    fig.subplots_adjust(left=0,right=1,bottom=.02,top=.94)
    light=np.asarray([0.34,-0.4,0.87]);light/=np.linalg.norm(light)
    merged_triangles = []
    merged_colours = []
    for name,solid,rgb in solids:
        verts, faces=solid.tessellate(tolerance=0.055, angularTolerance=0.20)
        pts=np.asarray([[p.x,p.y,p.z] for p in verts])
        faces=np.asarray(faces,dtype=int)
        tris=pts[faces]
        norms=np.cross(tris[:,1,:]-tris[:,0,:],tris[:,2,:]-tris[:,0,:])
        norms/=np.maximum(np.linalg.norm(norms,axis=1,keepdims=True),1e-9)
        factor=0.73 + 0.27*np.maximum(-0.2,np.dot(norms,light))
        colors=np.clip(np.asarray(rgb)[None,:]*factor[:,None],0,1)
        merged_triangles.extend(tris)
        merged_colours.extend(colors)
    # Use a single artist so matplotlib depth-sorts body and lead surfaces together.
    ax.add_collection3d(Poly3DCollection(merged_triangles, facecolors=merged_colours, edgecolors='none', zsort='average', zorder=2))
    ax.view_init(elev=39,azim=-130)
    ax.set_xlim(-3.95,3.95);ax.set_ylim(-3.55,3.55);ax.set_zlim(-0.40,2.25)
    ax.set_box_aspect((7.9,7.1,2.65))
    ax.set_axis_off()
    ax.text2D(.065,.93,'Jingdao ABS210',transform=ax.transAxes,fontsize=19,fontweight='bold',color='#202a35')
    ax.text2D(.065,.88,'LCSC C123897  |  ABS 4-lead SMD bridge rectifier',transform=ax.transAxes,fontsize=11,color='#46545e')
    ax.text2D(.065,.070,'Indexing recess on left edge (not a pin-1 dot)  •  6.20 mm lead span',transform=ax.transAxes,fontsize=10,color='#46545e')
    fig.savefig(OUT/(BASE+'_preview.png'),dpi=160,facecolor=fig.get_facecolor())
    plt.close(fig)
except Exception as e:
    print('Preview error:', e)

print('Exported',step_path, wrl_path)
print('Number of printable marks:',len(markings),'number of CAD solids:',len(solids))
print('Nominal leads:', [(i, round(s.Center().x,3),round(s.Center().y,3)) for i,s in leads])
