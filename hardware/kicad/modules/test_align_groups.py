import unittest
from types import SimpleNamespace

from kipy.geometry import Box2
from kipy.board_types import ArcTrack, Net, Track, Via

from align_groups import (
    connected_route_sets,
    connected_track_sets,
    copy_track,
    copy_via,
    group_local_vias,
)
from kicad_ipc import vector


def make_track(start, end, net="local", layer=0, width=250_000):
    track = Track()
    track.start = vector(*start)
    track.end = vector(*end)
    track.net = Net(name=net)
    track.layer = layer
    track.width = width
    return track


class AlignGroupsTrackTests(unittest.TestCase):
    def test_group_local_vias_finds_zone_connected_same_net_via(self):
        footprint = SimpleNamespace(
            definition=SimpleNamespace(
                pads=[SimpleNamespace(net=Net(name="zone-net"))]
            )
        )
        selected = Via()
        selected.position = vector(5, 5)
        selected.net = Net(name="zone-net")
        wrong_net = Via()
        wrong_net.position = vector(5, 5)
        wrong_net.net = Net(name="other")
        outside = Via()
        outside.position = vector(15, 5)
        outside.net = Net(name="zone-net")

        result = group_local_vias(
            Box2.from_xywh(0, 0, 10, 10),
            {"Q1": footprint},
            ["Q1"],
            [selected, wrong_net, outside],
        )

        self.assertEqual(result, [selected])

    def test_via_connects_tracks_on_different_layers(self):
        tracks = [
            make_track((0, 0), (10, 0), layer=0),
            make_track((10, 0), (20, 0), layer=31),
        ]
        via = Via()
        via.position = vector(10, 0)
        via.net = Net(name="local")

        sets = connected_route_sets(tracks, [via])

        self.assertEqual(len(sets), 1)
        self.assertEqual(len(sets[0][0]), 2)
        self.assertEqual(sets[0][1], [via])

    def test_connected_track_sets_require_same_net_and_layer(self):
        tracks = [
            make_track((0, 0), (10, 0)),
            make_track((10, 0), (20, 0)),
            make_track((10, 0), (10, 10), net="other"),
            make_track((10, 0), (10, -10), layer=31),
        ]

        sets = connected_track_sets(tracks)

        self.assertEqual(sorted(len(track_set) for track_set in sets), [1, 1, 2])

    def test_copy_track_preserves_properties_and_translates_geometry(self):
        source = make_track((1, 2), (3, 4), layer=31, width=400_000)
        source.locked = True

        copied = copy_track(source, 100, 200, Net(name="destination"))

        self.assertEqual((copied.start.x, copied.start.y), (101, 202))
        self.assertEqual((copied.end.x, copied.end.y), (103, 204))
        self.assertEqual(copied.net.name, "destination")
        self.assertEqual(copied.layer, source.layer)
        self.assertEqual(copied.width, source.width)
        self.assertTrue(copied.locked)
        self.assertFalse(copied.proto.HasField("id"))

    def test_copy_arc_translates_middle_point(self):
        source = ArcTrack()
        source.start = vector(0, 0)
        source.mid = vector(5, 5)
        source.end = vector(10, 0)
        source.net = Net(name="source")
        source.width = 300_000

        copied = copy_track(source, 7, 9, Net(name="destination"))

        self.assertEqual((copied.start.x, copied.start.y), (7, 9))
        self.assertEqual((copied.mid.x, copied.mid.y), (12, 14))
        self.assertEqual((copied.end.x, copied.end.y), (17, 9))
        self.assertEqual(copied.width, source.width)

    def test_copy_via_preserves_properties_and_translates_position(self):
        source = Via()
        source.position = vector(1, 2)
        source.net = Net(name="source")
        source.diameter = 700_000
        source.drill_diameter = 300_000
        source.locked = True

        copied = copy_via(source, 100, 200, Net(name="destination"))

        self.assertEqual((copied.position.x, copied.position.y), (101, 202))
        self.assertEqual(copied.net.name, "destination")
        self.assertEqual(copied.diameter, source.diameter)
        self.assertEqual(copied.drill_diameter, source.drill_diameter)
        self.assertTrue(copied.locked)
        self.assertFalse(copied.proto.HasField("id"))


if __name__ == "__main__":
    unittest.main()
