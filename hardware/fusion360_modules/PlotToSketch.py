# Author-
# Description-

import os
import re

import adsk.core
import adsk.fusion
import adsk.cam
import traceback


def normalisePoints(points: list[adsk.core.Point3D]) -> tuple[float, float]:
    minX = 100000000
    minY = 100000000

    # Get min (x, y)
    for p in points:
        if p.x < minX:
            minX = p.x
        if p.y < minY:
            minY = p.y

    # Normalise for min (x, y)
    for p in points:
        p.x = p.x - minX
        p.y = p.y - minY

    return minX, minY


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Set styles of file dialog.
        folderDlg = ui.createFolderDialog()
        folderDlg.title = 'Select the folder that contains the gerber files'

        # Show folder dialog
        dlgResult = folderDlg.showDialog()
        if dlgResult != adsk.core.DialogResults.DialogOK:
            return

        gerberFolder = folderDlg.folder

        edgeCutsFile = ""
        drillHolesFile = ""

        files = os.listdir(gerberFolder)
        for file in files:
            if file.endswith(".gm1"):
                edgeCutsFile = gerberFolder + '/' + file
            elif file.endswith(".drl"):
                drillHolesFile = gerberFolder + '/' + file

        if edgeCutsFile == "":
            ui.messageBox("Edge cuts file (extenstion .gm1) not found", "File not found")
            return

        if drillHolesFile == "":
            ui.messageBox("Drill holes file (extenstion .drl) not found", "File not found")
            return

        # Create a new document and get the Design.
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = app.activeProduct

        # Get the root component of the active design.
        rootComp = design.rootComponent

        # Create a new sketch on the XY construction plane.
        sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
        circles = sketch.sketchCurves.sketchCircles
        arcs = sketch.sketchCurves.sketchArcs

        edgePointPattern = r"^X([+-]{0,1}\d*)\s*Y([+-]{0,1}\d*)(D\d*)\*$"
        edgePointRe = re.compile(edgePointPattern)

        points = []
        prevXText = ""
        prevYText = ""

        with open(edgeCutsFile) as f:
            fileLines = f.readlines()

        for line in fileLines:
            if (line.startswith("X")):
                # Parse as a point
                m = edgePointRe.search(line)
                if (m != None):
                    xText = m.group(1)
                    yText = m.group(2)
                    if (xText != prevXText or yText != prevYText):
                        i = float(xText) / 1000000.0  # Convert to mm
                        y = float(yText) / 1000000.0  # Convert to mm
                        points.append(adsk.core.Point3D.create(i / 10.0, y / 10.0, 0))  # Convert point to cm
                        prevXText = xText
                        prevYText = yText

        minX, minY = normalisePoints(points)

        # Create edge cuts
        lines = sketch.sketchCurves.sketchLines
        for i in range(len(points) - 1):
            lines.addByTwoPoints(points[i], points[i + 1])

        toolSizePattern = r"^(T\d+)C([+-]?([0-9]*[.])?[0-9]+)$"
        toolSizeRe = re.compile(toolSizePattern)

        toolStartPattern = r"^(T\d+)$"
        toolStartRe = re.compile(toolStartPattern)

        holePattern = r"^X([+-]?([0-9]*[.])?[0-9]+)Y([+-]?([0-9]*[.])?[0-9]+)$"
        holeRe = re.compile(holePattern)

        toolPathPattern = r"^X([+-]?([0-9]*[.])?[0-9]+)Y([+-]?([0-9]*[.])?[0-9]+)G85X([+-]?([0-9]*[.])?[0-9]+)Y([+-]?([0-9]*[.])?[0-9]+)$"
        toolPathRe = re.compile(toolPathPattern)

        tools = {}
        currentToolSize = -1

        with open(drillHolesFile) as f:
            fileLines = f.readlines()

        for line in fileLines:
            # Check for tool definition
            m = toolSizeRe.search(line)
            if (m != None):
                toolName = m.group(1)
                toolSize = float(m.group(2))
                tools[toolName] = toolSize

            # Check for tool start
            m = toolStartRe.search(line)
            if (m != None and m.group(1) != "T0"):
                toolName = m.group(1)
                currentToolSize = tools[toolName]

            if currentToolSize >= 0.5:

                # Check for hole to drill
                m = holeRe.search(line)
                if (m != None):
                    x = float(m.group(1))
                    y = float(m.group(3))
                    point = adsk.core.Point3D.create(x / 10.0 - minX, y / 10.0 - minY, 0)
                    circles.addByCenterRadius(point, currentToolSize / 20.0)  # Convert diameter to radius and units to cm

                # Check for tool path
                m = toolPathRe.search(line)
                if (m != None):
                    x1 = float(m.group(1)) / 10.0 - minX
                    y1 = float(m.group(3)) / 10.0 - minY
                    x2 = float(m.group(5)) / 10.0 - minX
                    y2 = float(m.group(7)) / 10.0 - minY
                    radius = currentToolSize / 20.0
                    isHorz = x1 != x2

                    if isHorz:  # Horizontaol slot
                        dir = -1 if x1 > x2 else 1
                        p1 = adsk.core.Point3D.create(x1, y1 + radius * dir, 0)
                        p2 = adsk.core.Point3D.create(x1 - radius, y1, 0)
                        p3 = adsk.core.Point3D.create(x1, y1 + radius * -dir)
                        arcs.addByThreePoints(p1, p2, p3)
                        p4 = adsk.core.Point3D.create(x2, y2 + radius * -dir, 0)
                        p5 = adsk.core.Point3D.create(x2 + radius, y2, 0)
                        p6 = adsk.core.Point3D.create(x2, y2 + radius * dir)
                        arcs.addByThreePoints(p4, p5, p6)
                        lines.addByTwoPoints(p1, p6)
                        lines.addByTwoPoints(p3, p4)
                    else:  # Verical slot
                        dir = -1 if y1 > y2 else 1
                        p1 = adsk.core.Point3D.create(x1 + radius * dir, y1, 0)
                        p2 = adsk.core.Point3D.create(x1, y1 + radius, 0)
                        p3 = adsk.core.Point3D.create(x1 + radius * -dir, y1)
                        arcs.addByThreePoints(p1, p2, p3)
                        p4 = adsk.core.Point3D.create(x2 + radius * -dir, y2, 0)
                        p5 = adsk.core.Point3D.create(x2, y2 - radius, 0)
                        p6 = adsk.core.Point3D.create(x2 + radius * dir, y2)
                        arcs.addByThreePoints(p4, p5, p6)
                        lines.addByTwoPoints(p1, p6)
                        lines.addByTwoPoints(p3, p4)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
