C123897 / Jingdao ABS210 — Custom 3D Model for KiCad 10
======================================================

NOTCH-ENHANCED REVISION
A slightly wider and deeper semicircular indexing recess has been cut into
the left-hand top edge of the case (nominal visual radius 0.56 mm, depth
0.18 mm versus the previous radius 0.43 mm, depth 0.06 mm). The datasheet
does not dimension the notch; this is for viewing in KiCad, not tooling.
The lead and footprint alignment, body size, text orientation and model
origin are unchanged. No separate pin-1 dot has been added.

CONTENTS
- C123897_Jingdao_ABS210.step  : multicolour STEP assembly (mm)
- C123897_Jingdao_ABS210.wrl   : coloured VRML2 (KiCad units)
- C123897_Jingdao_ABS210_preview.png : 3D inspection preview
- make_C123897_model.py       : editable CadQuery model generator
- render_vtk.py               : optional VTK preview generator
- README.txt                  : these notes

COMPONENT
- LCSC number: C123897
- Manufacturer: Jingdao Microelectronics
- MPN: ABS210
- Description: 2A / 1000V 4-terminal surface-mount bridge rectifier
- Case: ABS/LBF
- Datasheet: https://www.lcsc.com/datasheet/C123897.pdf
- Dimension source: manufacturer datasheet, package-outline page 3

DIMENSIONS (NOMINAL, mm)
Plastic body X = 4.35 (allowed 4.2..4.5)
Plastic body Y = 5.05 (allowed 4.9..5.2)
Overall width across leads X = 6.20 (allowed 6.0..6.4)
Overall height Z = 1.40 (allowed 1.3..1.5)
Terminal width Y = 0.60 (allowed 0.5..0.7)
Rows of metal terminals Y = +/-2.00, i.e. 4.00 separation.
PCB datum Z=0.00 mm, origin centred over component.

IMPORTANT — PIN MAPPING
The drawing has four leads and a semicircular index notch on the plastic.
This is a visual model, not an electrical footprint or terminal mapping.
Because the ABS package has several variants, VERIFY that your footprint's
pads 1..4 match your specific manufacturer part's numbered terminals.
The manufacturer datasheet lists 1/2 as AC, 3 as + and 4 as -.
The placement of the notch/text must be checked against the PCB footprint.

ADDING TO LIBRARY FOOTPRINT (for every future instance)
1. Place STEP and WRL in a permanent shared 3D library folder.
2. Open the global/custom footprint in KiCad 10 Footprint Editor.
3. Footprint Properties -> 3D Models -> Add model.
4. Choose .step (or .wrl for the coloured VRML format).
5. Initial Scale (1,1,1), Rotation (0,0,0), Offset (0,0,0).
6. Check the 3D preview: terminal/pad positions and marking orientation.
   You can change Z rotation to 180 degrees if needed.
7. Save footprint in its library, then 'Update Footprints from Library'
   for any copies already on your PCB.

This design is a visually faithful nominal approximation, NOT official CAD.
Unspecified lead bends, fillet radii, top recess, font and ink are approximated.
No electrical/solderability guarantee is implied.
