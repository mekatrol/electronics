C5149193 / Texas Instruments LMR38020FDDAR — KiCad 10 3D model
================================================================

FILES
-----
C5149193_TI_LMR38020FDDAR.step         Coloured STEP solid assembly
C5149193_TI_LMR38020FDDAR.wrl          KiCad VRML2 shaded mesh
C5149193_TI_LMR38020FDDAR_preview.png   Rendered preview
make_C5149193_model.py                  Editable CadQuery generator
render_preview.py                       VTK preview generator

PACKAGE
-------
Manufacturer: Texas Instruments
Part number: LMR38020FDDAR
LCSC: C5149193
Package: HSOIC-8 / SO PowerPAD-8, TI DDA0008B
Main marking: C3802F (not the full ordering code)
Pin 1: small modelled, recessed location dot, adjacent to lead #1

CAD GEOMETRY, NOMINAL (MM)
--------------------------
Body length (Y): 4.90
Body width  (X): 3.90
Overall lead X span: 6.00 (drawing allowable 5.8–6.2)
Model Z height: 1.66 (drawing max 1.70)
Lead pitch Y: 1.27
Terminal metal width: 0.41 (drawing allowable 0.31–0.51)
Exposed thermal pad: 2.41 X x 3.10 Y
Bottom of leads and exposed pad: Z = 0
3D model origin: (0,0,0) at geometric footprint centre on PCB top
Scale factor in KiCad: 1,1,1; model rotation: 0,0,0 to start.

TOP VIEW ORIENTATION
--------------------
When 'C3802F' is readable and +Y points upward:

   #1 GND  -|  dot o [ C3802F ]  |-  #8 SW
   #2 EN   -|                   |-  #7 BOOT
   #3 VIN  -|                   |-  #6 PG
   #4 RT   -|___________________|-  #5 FB

The thermal pad at the centre of the underside must be connected to
system ground per the IC datasheet.

KI CAD 10 LIBRARY INSTALL
-------------------------
1. In Footprint Editor open your custom GLOBAL library footprint. If using
   a stock library, duplicate the footprint into your own .pretty library.
2. Open Footprint Properties -> 3D Models.
3. Add this .step file, preferably using the KiCad 10 Embed File option to
   make the model portable inside the library footprint. Alternatively,
   use the .wrl file for shading when KiCad uses that format.
4. Check model orientation and XY alignment against pads 1-8 and the exposed
   pad. Start with rotation / scale / offsets at 0 / 1 / 0, respectively.
5. Save the LIBRARY footprint. Existing board instances may need
   Tools -> Update Footprints from Library in PCB Editor.

A KiCad package matching the general dimensions is:
Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm
Check its actual pad numbering and copper land size for this device.

MODEL APPROXIMATIONS
--------------------
The main envelope, lead pitch, pad size and pin indexing derive from TI's
DDA0008B package outline (4214849/B). The chamfers, mould radii, bending
profile, marking thickness and dot size are illustrative and are not TI
specified manufacturing dimensions. This model is for 3D visualization and
clearance checks, not for replacing electrical/PCB manufacturing validation.

DATASHEET
---------
https://www.lcsc.com/datasheet/C5149193.pdf
https://www.ti.com/lit/ds/symlink/lmr38020.pdf
Texas Instruments datasheet section 6 (pin order), package outline p.37,
package option addendum (part marking C3802F).
