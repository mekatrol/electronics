# cp D:\repos\HomeAutomation\hardware\kicad_modules\layout_outputs_plugin.py C:\Users\Dad\Documents\KiCad\6.0\scripting\plugins\layout_outputs_plugin.py

from pcbnew import *

# board = GetBoard()
# tracks = board.GetTracks()
# pads = board.GetPads()
# selected_tracks = [t for t in board.GetTracks() if t.IsSelected()]
#
# j6 = board.FindFootprintByReference('J6')
# j6_pads = j6.Pads()
# for pad in j6_pads:
#     print(pad.GetNetname())

# j6_pad = j6_pads[len(j6_pads) - 1]
# j6_pad.GetPadName()
# j6_net = j6_pad.GetNet()
# for track in tracks:
#   if track.GetNetname().startswith('/Outputs/OP1'):
#       print(track.GetNetname())
#
# j6_connected = con.GetConnectedTracks(j6_pad)
# for c in j6_connected:
#       print(c.GetName())

# for pad in pads:
#   if pad.GetNetname().startswith('GND'):
#       print(pad.GetNetname())
#       print(pad.GetNetCode())
#       print(pad.GetClass())
#

# d15 = board.FindFootprintByReference('D15')
# d15_pads = d15.Pads()
# for pad in d15_pads:
#   if pad.GetNetname().startswith('/Outputs/OP1'):
#       print(pad.GetNetname())
#
# d15_pad = d15_pads[len(d15_pads) - 1]
# d15_pad.GetPadName()

# board.FindNet("GND")


def GetTrackFromName(name):
    for track in tracks:
        if track.GetNetname() == name:
            print(f"Found '{track.GetNetname()}'")
            return track

# for pad in d15.Pads():
#   track = GetTrackFromName(pad.GetNetname())
#   if not track is None:
#       board.Remove(track)


class FootPrintRef:
    orientation = 0
    offset = wxPoint(0, 0)

    ref_text = ''
    ref_text_offset = wxPoint(0, 0)
    ref_text_angle = 0


class TriacFetLayoutPlugin(ActionPlugin):
    def defaults(self):
        self.name = "Layout Triac/FET outputs"
        self.category = "Mekatrol"
        self.description = "Layout Triac/FET outputs relative to connector"
        self.board = GetBoard()

    def Run(self):
        # Define component set references, the first element is the one to reference from
        # op1_refs = ["J6",  "D18", "D15", "D12", "JP1",  "Q1", "R8",  "R11", "JP4"]
        # op2_refs = ["J7",  "D19", "D16", "D13", "JP2",  "Q2", "R9",  "R12", "JP5"]
        # op3_refs = ["J8",  "D20", "D17", "D14", "JP3",  "Q3", "R10", "R13", "JP6"]
        # op4_refs = ["J9",  "D27", "D24", "D21", "JP7",  "Q4", "R14", "R17", "JP10"]
        # op5_refs = ["J10", "D28", "D25", "D22", "JP8",  "Q5", "R15", "R18", "JP11"]
        # op6_refs = ["J11", "D29", "D26", "D23", "JP9",  "Q6", "R16", "R19", "JP12"]
        # op7_refs = ["J12", "D34", "D32", "D30", "JP13", "Q7", "R20", "R22", "JP15"]
        # op8_refs = ["J13", "D35", "D33", "D31", "JP14", "Q8", "R21", "R23", "JP16"]

        op1_refs = ["D16", "R15", "R18", "JP8"]
        op2_refs = ["D17", "R16", "R19", "JP9"]
        op3_refs = ["D18", "R17", "R20", "JP10"]
        op4_refs = ["D25", "R21", "R24", "JP14"]
        op5_refs = ["D26", "R22", "R25", "JP15"]
        op6_refs = ["D27", "R23", "R26", "JP16"]
        op7_refs = ["D33", "R27", "R29", "JP19"]
        op8_refs = ["D34", "R28", "R30", "JP20"]

        fp_refs = self.MeasureRelativePositions(op1_refs)

        self.SetRelativePositions(op2_refs, fp_refs)
        self.SetRelativePositions(op3_refs, fp_refs)
        self.SetRelativePositions(op4_refs, fp_refs)
        self.SetRelativePositions(op5_refs, fp_refs)
        self.SetRelativePositions(op6_refs, fp_refs)
        self.SetRelativePositions(op7_refs, fp_refs)
        self.SetRelativePositions(op8_refs, fp_refs)

        Refresh()

    def MeasureRelativePositions(self, refs):
        if len(refs) < 2:
            print(f"****** ERROR: At least two references needed...")
            return []

        # The first element in the set is the footprint ref to reference position from
        relative_to_ref = refs[0]

        # Get the remaining references in the set
        remaining_refs = refs[1:]

        # Get the footprint for the reference poistion ref
        relative_footprint = self.board.FindFootprintByReference(relative_to_ref)

        # Create empty set of empty positions
        fp_refs = []

        # Enumerate the reamining reference footprints
        for ref in remaining_refs:
            # Get the footprint
            ref_footprint = self.board.FindFootprintByReference(ref)

            # Error if not found
            if ref_footprint is None:
                print(f"****** ERROR: Footprint with ref '{ref}' not found...")
                return []
            else:
                footprint_ref = ref_footprint.Reference()

                fp_ref = FootPrintRef()
                fp_ref.offset = relative_footprint.GetPosition() - ref_footprint.GetPosition()
                fp_ref.orientation = ref_footprint.GetOrientation()
                fp_ref.ref_text = ref
                fp_ref.ref_text_offset = ref_footprint.GetPosition() - footprint_ref.GetPosition()
                fp_ref.ref_text_angle = footprint_ref.GetTextAngle()

                fp_refs.append(fp_ref)

        return fp_refs

    def SetRelativePositions(self, refs, fp_refs):
        # The first element in the set is the footprint ref to reference position from
        relative_to_ref = refs[0]

        # Get the remaining footprint references in the set
        remaining_fp_refs = refs[1:]

        # Get the footprint for the reference poistion ref
        relative_footprint = self.board.FindFootprintByReference(relative_to_ref)

        # Get control position
        control_position = relative_footprint.GetPosition()
        print(f"Control position ref component: '{relative_to_ref}' is '{control_position}'")

        for idx, ref in enumerate(remaining_fp_refs):
            # Get the footprint
            ref_footprint = self.board.FindFootprintByReference(ref)

            # Get footprint offse and orientation info
            fp_ref = fp_refs[idx]

            # Set footprint orientation
            ref_footprint.SetOrientation(fp_ref.orientation)

            # Add to control position
            new_position = control_position - fp_ref.offset

            print(f"Moving '{ref} from '{ref_footprint.GetPosition()}' to '{new_position}' using offset '{fp_ref.offset}'")

            # Set the position relative to the reference position
            ref_footprint.SetPosition(new_position)

            text = ref_footprint.Reference()
            text.SetTextAngle(fp_ref.ref_text_angle)
            text.SetPosition(ref_footprint.GetPosition() - fp_ref.ref_text_offset)


TriacFetLayoutPlugin().register()
