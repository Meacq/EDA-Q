from gdspy import *
from OCC.Core import gp, BRepBuilderAPI

# autopep8: off
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../"))
import toolbox
from api.gds import Gds
# autopep8: on


class VisitedPoints:
    def __init__(self):
        self._points = []
        pass

    def __setitem__(self, index, value):
        self._points.append((index, value))

    def __getitem__(self, index):
        value = None
        for i in self._points:
            if i[0].IsEqual(index, 1e-16):
                return i[1]
        return value

    def __delitem__(self, index):
        for (idx, i) in enumerate(self._points):
            if i[0].IsEqual(index, 1e-16):
                del self._points[idx]
                return

    def __contains__(self, item: gp.gp_Pnt):
        check = False
        for i in self._points:
            if item.IsEqual(i[0], 1e-16):
                return True
        return check


def split_path_into_rings(points):
    """
    split gds polygon points to outer rings and inner rings,
    for occ can not support self intersection polygons.

    :param points: gds polygon points
    :return: list constains outer rings and inner rings
    """
    rings = []
    current_ring = []
    visited_points = VisitedPoints()

    for point in points:
        if point not in visited_points:
            # if current point is not visited, append to current rings
            current_ring.append(point)
            visited_points[point] = len(current_ring) - 1
        else:
            # if repeat point visited, a hole found
            start_index = visited_points[point]
            ring = current_ring[start_index:]
            rings.append(ring)

            # move out hole points
            current_ring = current_ring[:start_index]
            for p in ring:
                del visited_points[p]

    # append outter ring
    if current_ring:
        rings.append(current_ring)

    return rings


def create_wire_from_points(point_list):
    """Helper function to create a closed wire from a list of gp_Pnt"""
    builder = BRepBuilderAPI.BRepBuilderAPI_MakePolygon()
    for pt in point_list:
        builder.Add(pt)
    builder.Close()  # Ensure the wire is closed
    return builder.Wire()


class GdsLibTool:
    def convertLibToShape(gds_lib: GdsLibrary):
        shapes = []
        for _, cell in gds_lib.cells.items():
            shapes.extend(GdsLibTool.convertCellToShape(cell))
        return shapes

    def convertCellToShape(gds_cell: Cell):
        shapes = []
        for polygonset in gds_cell.polygons:
            for (idx, polygon_pts) in enumerate(polygonset.polygons):
                gp_points = [gp.gp_Pnt(p[0], p[1], 0) for p in polygon_pts]
                rings = split_path_into_rings(gp_points)
                outter_ring = rings.pop()
                face_builder = BRepBuilderAPI.BRepBuilderAPI_MakeFace(
                    create_wire_from_points(outter_ring))
                for r in rings:
                    if len(r) >= 3:
                        face_builder.Add(create_wire_from_points(r))
                shapes.append(
                    (face_builder.Face(), polygonset.layers[idx], polygonset.datatypes[idx]))
        return shapes

    def convertDesignDdsToCell(design_gds: Gds):
        components = []
        cells = []
        for cmpnts_name in design_gds.cmpnts_name_list:
            cmpnts = getattr(design_gds, cmpnts_name)
            # cmpnts.draw_gds()
            for cmpnt_name in cmpnts.cmpnt_name_list:
                cmpnt = getattr(cmpnts, cmpnt_name)
                components.append(cmpnt)
                cmpnt.draw_gds()
                layer_num = toolbox.custom_hash(
                    cmpnt.chip if hasattr(cmpnt, "chip") else "None")
                cells.append(cmpnt.cell.flatten(
                    single_layer=layer_num, single_datatype=0))
        return [components, cells]
