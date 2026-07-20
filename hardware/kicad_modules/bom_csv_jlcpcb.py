"""
    @package
    Generate a JLCPCB CSV BOM.
    LCSC Part numbers are copied from the "LCSC Part #" field.
    Hide components from the BOM by setting the "LCSC Part #" field to an empty string.

    Output fields:
    'Comment', 'Designator', 'Footprint', 'LCSC Part #'

    Command line:
    python "pathToFile/bom_csv_jlcpcb.py" "%I" "%O.csv"
"""

import kicad_netlist_reader
import csv
import sys

net = kicad_netlist_reader.netlist(sys.argv[1])

with open(sys.argv[2], "w", newline="") as f:
    out = csv.writer(f)
    out.writerow(["Comment", "Designator", "Footprint", "LCSC Part Number"])

    for group in net.groupComponents():
        refs = []

        lcsc_part_number = ""

        # Build row data for each component type
        for component in group:
            # Ignore if no LCSC part number
            if component.getField("LCSC Part #") == "":
                continue

            # Add components referenced
            refs.append(component.getRef())

            # Add LCSC part number
            lcsc_part_number = component.getField("LCSC Part #") or lcsc_part_number
            c = component

        # Ignore this componet if it was not referenced in the design
        if len(refs) == 0:
            continue

        # Write component row data
        out.writerow(
            [
                c.getValue() + " " + c.getDescription(),
                ",".join(refs),
                c.getFootprint().split(":")[1],
                lcsc_part_number,
            ]
        )

    f.close()
