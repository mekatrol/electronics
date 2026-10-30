C278365 - SUMIDA CDRH129RNP-330MC
Custom 3D model for KiCad 10
================================

PART IDENTIFICATION
 LCSC:           C278365
 Manufacturer:   Sumida
 MPN:            CDRH129RNP-330MC
 Type:           SMD shielded power inductor, 33 uH
 Nominal stamp:  330
 Terminals:      two, non-polarized

MODEL GEOMETRY / REFERENCE
 Manufacturer series CDRH129R dimensions (10-56 uH variant):
   Ferrite shield nominal envelope        12.0 x 12.0 mm
   Manufacturer allowed body tolerance    +/- 0.4 mm
   Maximum height                         10.0 mm
   Two underside plated terminal areas     5.0 +/- 0.3 mm wide
                                         x 1.4 +/- 0.3 mm deep
   Recommended PCB land pattern:          5.7 x 2.6 mm per pad
   Recommended pad centre spacing:        10.4 mm

 3D MODEL SPECIFIC
   Total X range:                         -6.000 ... +6.000 mm
   Total Y range:                         -6.025 ... +6.025 mm
   Total Z range:                           0.000 ... +9.759 mm
   3D terminal landing centre X:            0.00 mm
   3D terminal landing centre Y:           +/-5.25 mm
   Axis alignment: terminal pads at the top/bottom of XY top view (+/-Y)
   Reference orientation: top stamp '330' readable with +Y upwards
   KiCad reference origin: footprint centre on board surface Z=0

APPLICATION IN KICAD 10
 1. Open your custom library footprint in Footprint Editor.
 2. Footprint Properties > 3D Models > Add file.
 3. Use the STEP or WRL file. You may tick 'Embed File' to store
    the model within the footprint library itself.
 4. Initially set Scale=1,1,1; Offset=0,0,0; Rotation=0,0,0.
 5. Confirm that copper pads align with the model's two terminals.
    If the footprint's pads are on left/right instead of top/bottom,
    set a 90-degree rotation around Z.
 6. Save the library footprint. Update any already-placed instances
    using Tools > Update Footprints from Library.

FILES
 C278365_Sumida_CDRH129RNP-330MC.step       CAD solid, mm units
 C278365_Sumida_CDRH129RNP-330MC.wrl        VRML2, coloured for KiCad
 C278365_Sumida_CDRH129RNP-330MC_preview.png  Render including terminal underside
 make_C278365_model.py                     Editable CadQuery model source
 render_preview.py                         Preview rendering source

NOTES
 The body, ferrite core texture/shape, side metal wrap and marking are
 visual approximations, not a supplier-provided production CAD model.
 STEP read-back was tested with CadQuery/OpenCascade. Rendering was tested
 using VTK. Files were not tested in a running KiCad 10 installation.

 DATASHEET
 https://www.lcsc.com/datasheet/C278365.pdf
 https://products.sumida.com/products/pdf/CDRH129R_2024July.pdf

 The downloadable models use the same file naming scheme and VRML scaling
 as earlier models created for this user's KiCad 10 footprint library.
