from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QFileDialog
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPoint, QStandardPaths

from OCC.Display.OCCViewer import Viewer3d
from OCC.Core import gp, BRepBuilderAPI, Quantity, BRepOffsetAPI
from OCC.Core import STEPControl

import pandas as pd
from enum import IntEnum
from manufac_sim_widget import ManufacSimWidget
from gdspy import *
from gds_editor_tool.gds_topods import GdsLibTool

# autopep8: off
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../"))
import toolbox
from api.gds import Gds
# autopep8: on

class GdsEditor(QWidget):

    class ComponentData:
        def __init__(self):
            self.component = None
            self.gdscell = None
            self.topo_shape = None
            self.ais_shape = None

    class Action(IntEnum):
        SHOW_IN_INTERPRETER = 0
        SAVE_FILE = 1
        SHOW_MANUFACTURING_SIM = 2

    sendObjToInterpreter = pyqtSignal(dict)

    class RightButtonMenu(QMenu):
        """
        Menu for right click
        """
        action_triggered = pyqtSignal(int, QPoint)

        def __init__(self, parent=None):
            QMenu.__init__(self, parent)
            self.cur_pos = None
            self.addAction("Show in interpreter").triggered.connect(
                lambda check, self=self: self.action_triggered.emit(GdsEditor.Action.SHOW_IN_INTERPRETER.value, self.cur_pos))
            self.addAction("Save current layout to file").triggered.connect(
                lambda check, self=self: self.action_triggered.emit(GdsEditor.Action.SAVE_FILE.value, self.cur_pos))
            self.addAction("Open manufacturing simulation").triggered.connect(
                lambda check, self=self: self.action_triggered.emit(GdsEditor.Action.SHOW_MANUFACTURING_SIM.value, self.cur_pos))

        def popup(self, p, action=None):
            self.cur_pos = p
            return super().popup(p, action)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        # enable Mouse Tracking
        self.setMouseTracking(True)

        # Strong focus
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)

        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_PaintOnScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        self.setAutoFillBackground(False)

        self.right_menu = GdsEditor.RightButtonMenu(self)
        self.right_menu.action_triggered.connect(self.handleMenuAction)

        # use digraph to store component and shape relation
        self.component_map = pd.DataFrame(
            columns=['component', 'cell', 'topo_shape', 'ais_shape'])

        # occ 3dviewer
        self._display = Viewer3d()
        self._display.Create(window_handle=int(
            self.winId()), parent=self, create_default_lights=False, display_glinfo=False)
        # background gradient
        self._display.SetModeShaded()
        # fix top view
        self._display.View_Top()
        self._display.set_bg_gradient_color([0, 10, 10], [0, 10, 10])

        self._pan_start_x = None
        self._pan_start_y = None
        self._drawbox = False

        self.dragStartPosX = None
        self.dragStartPosY = None

        self._move_start_x = None
        self._move_start_y = None

        self._selected_shape = None

        # manufacting setting
        self._sim_widget = ManufacSimWidget(self)
        self._sim_widget.setVisible(False)
        self._in_sim_mode = False

        self._sim_widget.applySimData.connect(self.manufacSim)
        self.resize(self.maximumSize())

    def reset(self):
        self._selected_shape = None
        self._in_sim_mode = False
        self._display.EraseAll()
        self._display.Repaint()
        self.component_map = pd.DataFrame()

    def sizeHint(self):
        return QSize(800, 600)

    def handleMenuAction(self, action, pos):
        '''
        process right mouse button menu action
        '''
        lpos = self.mapFromGlobal(pos)

        if action == GdsEditor.Action.SHOW_IN_INTERPRETER:
            self._display.Select(lpos.x(), lpos.y())
            selected_shape = self._display.Context.SelectedInteractive()
            if selected_shape is not None:
                self._display.Context.ClearSelected(True)
                component = self.component_map[self.component_map['ais_shape']
                                               == selected_shape].iat[0, 0]
                self.sendObjToInterpreter.emit({"selec_component": component})
        elif action == GdsEditor.Action.SAVE_FILE:
            save_fn, _ = QFileDialog.getSaveFileName(
                None, "Save File", QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation), ".step")
            if save_fn:
                self.saveCurrentLayoutAsSTEP(save_fn)
            else:
                return
        elif action == GdsEditor.Action.SHOW_MANUFACTURING_SIM:
            datas = []
            marked_layer_type = set()
            for i in range(len(self.component_map)):
                cell = self.component_map.iat[i, 1]
                for polygon in cell.polygons:
                    if type(polygon) == Path:
                        layer = polygon.layers[0]
                        datatype = polygon.datatypes[0]
                    elif type(polygon) == PolygonSet:
                        layer = polygon.layers[0]
                        datatype = polygon.datatypes[0]
                    else:
                        pass
                    if (layer, datatype) not in marked_layer_type:
                        marked_layer_type.add((layer, datatype))
                        color = Quantity.Quantity_Color(layer+datatype)
                        r, g, b = int(color.Red()*255), int(color.Green()
                                                            * 255), int(color.Blue()*255)
                        rgb = f"#{r:02x}{g:02x}{b:02x}".upper()
                        datas.append(
                            {'Color': rgb, 'Layer': layer, 'Datatype': datatype})
            self._sim_widget.setData(datas)
            self._sim_widget.show()
            pass

    def saveCurrentLayoutAsSTEP(self, fn):
        writer = STEPControl.STEPControl_Writer()
        for i in range(len(self.component_map)):
            ais_shape = self.component_map.iat[i, 3]
            topo_shape = ais_shape.Shape()
            trans = ais_shape.Transformation()
            transformer = BRepBuilderAPI.BRepBuilderAPI_Transform(trans)
            transformer.Perform(topo_shape)
            writer.Transfer(
                transformer.Shape(), STEPControl.STEPControl_StepModelType.STEPControl_AsIs)

        writer.Write(fn)

    def resizeEvent(self, event):
        super(GdsEditor, self).resizeEvent(event)
        self._display.View.MustBeResized()

    def paintEngine(self):
        return None

    def keyPressEvent(self, event):
        super(GdsEditor, self).keyPressEvent(event)

    def focusInEvent(self, event):
        self._display.View.MustBeResized()
        self._display.Repaint()

    def focusOutEvent(self, event):
        self._display.View.MustBeResized()
        self._display.Repaint()

    def paintEvent(self, event):
        self._display.Context.UpdateCurrentViewer()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        zoom_factor = 1.25 if delta > 0 else 0.75
        self._display.ZoomFactor(zoom_factor)

    def mousePressEvent(self, event):
        pos = event.pos()
        button = event.button()
        # use left mouse button to pan
        if button == Qt.MouseButton.LeftButton:
            if self._in_sim_mode:
                self.dragStartPosX = pos.x()
                self.dragStartPosY = pos.y()
                self._display.StartRotation(
                    self.dragStartPosX, self.dragStartPosY)
            else:
                self._pan_start_x = pos.x()
                self._pan_start_y = pos.y()
        # use middle mouse button to move component
        elif button == Qt.MouseButton.MiddleButton:
            self._move_start_x = pos.x()
            self._move_start_y = pos.y()
            self._display.Context.ClearSelected(True)
            self._display.Select(pos.x(), pos.y())
            self._selected_shape = self._display.Context.SelectedInteractive()
        # right mouse button pop menu
        elif button == Qt.MouseButton.RightButton:
            gpos = self.mapToGlobal(pos)
            self.right_menu.popup(gpos)

    def mouseMoveEvent(self, event):
        pos = event.pos()
        buttons = event.buttons()
        # use left mouse button to pan
        if buttons == Qt.MouseButton.LeftButton:
            if self._in_sim_mode:
                self._display.Rotation(pos.x(), pos.y())
            else:
                dx = pos.x() - self._pan_start_x
                dy = pos.y() - self._pan_start_y
                self._pan_start_x = pos.x()
                self._pan_start_y = pos.y()
                self._display.Pan(dx, -dy)
        if buttons == Qt.MouseButton.MiddleButton and self._selected_shape:
            # translate view coord to real coord
            view = self._display.View
            v1 = view.Convert(self._move_start_x, self._move_start_y)
            v2 = view.Convert(pos.x(), pos.y())
            move_vec = gp.gp_Vec(
                gp.gp_Pnt(v1[0], v1[1], 0), gp.gp_Pnt(v2[0], v2[1], 0))
            trsf = gp.gp_Trsf()
            trsf.SetTranslation(move_vec)
            self._selected_shape.SetLocalTransformation(
                self._selected_shape.Transformation()*trsf)
            self._display.Context.Update(self._selected_shape, True)

            self._move_start_x = pos.x()
            self._move_start_y = pos.y()
        else:
            self._display.MoveTo(pos.x(), pos.y())

    def mouseReleaseEvent(self, event):
        button = event.button()
        if button == Qt.MouseButton.MiddleButton:
            self._selected_shape = None
            self._display.Context.ClearSelected(True)

    def showTopoDS(self, component: list):
        for i in component:
            for s in i.shapes:
                self._display.DisplayShape(
                    s, color=Quantity.Quantity_NameOfColor.Quantity_NOC_CORAL, transparency=0.8)
        self._display.FitAll()

    def showDesignGds(self, design_gds: Gds):
        """plot gds from design

        Args:
            design_gds (Gds): _description_
        """
        self.reset()
        [cmpnts, cells] = GdsLibTool.convertDesignDdsToCell(design_gds)

        for idx, cmpnt in enumerate(cmpnts):
            cell = cells[idx]
            shapes = GdsLibTool.convertCellToShape(cell)
            for (topo_shape, layer, datatype) in shapes:
                ais_shapes = self._display.DisplayShape(
                    topo_shape, color=Quantity.Quantity_NameOfColor(layer+datatype), transparency=0.8)
                for a in ais_shapes:
                    temp = pd.DataFrame(
                        [{'component': cmpnt, 'cell': cell, 'topo_shape': topo_shape, 'ais_shape': a}])
                    self.component_map = pd.concat(
                        [self.component_map, temp], ignore_index=True)
        self._display.FitAll()

    def showComponents(self, components: list):
        self.reset()
        for cmpnt in components:
            cmpnt.draw_gds()
            layer_num = toolbox.custom_hash(
                cmpnt.chip if hasattr(cmpnt, "chip") else "None")
            cmpnt.cell.flatten(single_layer=layer_num, single_datatype=0)
            shapes = GdsLibTool.convertCellToShape(cmpnt.cell)
            for (topo_shape, layer, datatype) in shapes:
                ais_shapes = self._display.DisplayShape(
                    topo_shape, color=Quantity.Quantity_NameOfColor(layer+datatype), transparency=0.8)
                for a in ais_shapes:
                    temp = pd.DataFrame(
                        [{'component': cmpnt, 'cell': cmpnt.cell, 'topo_shape': topo_shape, 'ais_shape': a}])
                    self.component_map = pd.concat(
                        [self.component_map, temp], ignore_index=True)
        self._display.FitAll()

    def updateComponent(self, comp):
        result = self.component_map[self.component_map['component'] == comp]
        ais_shape = result.iat[0, 3]
        # save trans
        trans = ais_shape.Transformation()
        self._display.Context.Erase(ais_shape, False)
        layer_num = toolbox.custom_hash(
            comp.chip if hasattr(comp, "chip") else "None")
        new_cell = comp.cell.flatten(single_layer=layer_num, single_datatype=0)
        shapes = GdsLibTool.convertCellToShape(new_cell)
        for (new_topo_shape, layer, datatype) in shapes:
            new_ais_shape = self._display.DisplayShape(
                new_topo_shape, color=Quantity.Quantity_NameOfColor(layer+datatype), transparency=0.8)
            # apply transformation to new shape
            for a in new_ais_shape:
                a.SetLocalTransformation(trans)
                result.iat[0, 1] = new_cell
                result.iat[0, 2] = new_topo_shape
            result.iat[0, 3] = a
        self._display.FitAll()

    def drawSelectBox(self, event):
        tolerance = 2
        pt = event.pos()
        dx = pt.x() - self.dragStartPosX
        dy = pt.y() - self.dragStartPosY
        if abs(dx) <= tolerance and abs(dy) <= tolerance:
            return
        self._drawbox = [self.dragStartPosX, self.dragStartPosY, dx, dy]

    def saveImage(self, path: str = None):
        self._display.ExportToImage(path)

    def manufacSim(self, process: list):
        current_upper = 0
        current_lower = 0
        for p in process:
            layer = int(p["Layer"])
            datatype = int(p['Datatype'])
            proc = p['Process']
            depth = float(p['Depth'])
            for i in range(len(self.component_map)):
                cell = self.component_map.iat[i, 1]
                if cell.layer == layer and cell.datatype == datatype:
                    topo_shape = self.component_map.iat[i, 2]
                    ais_shape = self.component_map.iat[i, 3]
                    trans = ais_shape.Transformation()
                    if proc == "CVD":
                        norm_line = BRepBuilderAPI.BRepBuilderAPI_MakeEdge(
                            gp.gp_Pnt(0, 0, current_upper), gp.gp_Pnt(0, 0, current_upper+depth)).Edge()
                        current_upper += depth
                    else:
                        norm_line = BRepBuilderAPI.BRepBuilderAPI_MakeEdge(
                            gp.gp_Pnt(0, 0, current_lower), gp.gp_Pnt(0, 0, current_lower-depth)).Edge()
                        current_lower -= depth
                    spine = BRepBuilderAPI.BRepBuilderAPI_MakeWire(
                        norm_line).Wire()
                    new_topo_shape = BRepOffsetAPI.BRepOffsetAPI_MakePipe(
                        spine, topo_shape).Shape()
                    self._display.Context.Erase(ais_shape, False)
                    new_ais_shape = self._display.DisplayShape(
                        new_topo_shape, color=Quantity.Quantity_NameOfColor(cell.layer+cell.datatype), transparency=0.8)

                    for a in new_ais_shape:
                        a.SetLocalTransformation(trans)
                        self.component_map.iat[i, 3] = a

                    self._in_sim_mode = True


if __name__ == "__main__":
    import sys
    import os
    from PyQt5.QtWidgets import QVBoxLayout, QMainWindow
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
    from OCC.Core import BRepOffsetAPI, GeomAbs
    current_path = os.path.dirname(os.path.abspath(__file__))
    PROJ_PATH = os.path.abspath(os.path.join(
        os.path.dirname(current_path), "../.."))
    sys.path.append(PROJ_PATH)
    from library.qubits import transmon
    from library.readout_lines import *
    from library.coupling_lines import coupling_line_straight
    from GUI.gui_modules.Command.Python_Interpreter import PythonInterpreter

    from api.design import Design

    design = Design()
    design.generate_topology(topo_col=3, topo_row=3)
    design.topology.generate_random_edges(edges_num=1500)
    design.generate_qubits(topology=True, qubits_type="Transmon", chip_name="chip0", dist=3000)
    design.generate_chip(qubits=True, dist=4000)
    design.generate_readout_lines(qubits=True)
    design.routing(method="Control_off_chip_routing", chip_name="chip0")

    app = QApplication([])
    main_w = QMainWindow()

    vlayout = QVBoxLayout()
    main_widget = QWidget()
    main_widget.setLayout(vlayout)

    main_w.setCentralWidget(main_widget)

    viewer = GdsEditor()
    viewer.setBaseSize
    vlayout.addWidget(viewer, 3)
    qubit = transmon.Transmon({})
    cpl = coupling_line_straight.CouplingLineStraight({})

    viewer.showDesignGds(design.gds)
    qub = transmon.Transmon(options=(0,0))
    qub.draw_gds()
    qub.save_gds()
    # viewer.showComponents([qub])
    pyinp = PythonInterpreter()
    pyinp.addLocalsVar({"viewer":  viewer})
    pyinp.clear_output()
    viewer.sendObjToInterpreter.connect(pyinp.addLocalsVar)
    vlayout.addWidget(pyinp, 1)
    main_w.show()
    sys.exit(app.exec_())
