import sys
from PyQt5 import uic
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPen, QPolygon, QBrush, QColor
from PyQt5 import QtCore, QtWidgets

from image_viewer import ImageViewer
from roofeus import models as rfsm
from roofeus import utils as rfsu

Ui_MainWindow, QtBaseClass = uic.loadUiType("ui/main.ui")
VALID_FORMAT = ('.BMP', '.GIF', '.JPG', '.JPEG', '.PNG', '.PBM', '.PGM', '.PPM', '.TIFF', '.XBM')


class TemplateEditor(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.template = rfsm.RFTemplate()

        self.image_viewer = ImageViewer(self.qlabel_image)
        self.image_viewer_faces = ImageViewer(self.qlabel_image_faces)
        self.vertex_x_w.setMaximum(1.00)
        self.vertex_x_w.setDecimals(3)
        self.vertex_x_w.setSingleStep(0.001)
        self.vertex_y_w.setMaximum(1.00)
        self.vertex_y_w.setDecimals(3)
        self.vertex_y_w.setSingleStep(0.001)

        self.__connect_events()
        self.show()

        # Common tab vars
        self.dirty_vertex_ids = False
        self.last_valid_face_list = self.template.faces
        self.last_valid_vertex_count = self.template.vertex_count

        # Vertex tab vars
        self.draw_temporal_vertex = False
        self.temporal_vertex_pos = ()

        # Face tab vars
        self.image_viewer_faces.paint_repeated = 2
        self.display_repeated_faces = True

    # Private actions
    def __connect_events(self):

        # Menu actions
        self.action_open_template.triggered.connect(self.open_template)
        self.action_save_template.triggered.connect(self.save_template)
        self.action_open_texture.triggered.connect(self.open_texture)

        # Image viewer listeners (vertex)
        self.image_viewer.add_over_image_drawer(self.vertex_image_drawer)
        self.image_viewer.add_left_click_listener(self.ivv_draw_temporal_vertex)
        self.image_viewer.add_move_listener(self.move_temporal_vertex)
        self.image_viewer.add_left_release_listener(self.add_vertex)
        self.image_viewer.add_right_click_listener(self.cancel_vertex)
        self.image_viewer.add_right_click_listener(self.select_nearest_vertex)

        # Image viewer listeners (faces)
        self.image_viewer_faces.add_over_image_drawer(self.faces_image_drawer)
        self.image_viewer_faces.add_left_click_listener(self.select_nearest_vertex_in_quad)
        self.image_viewer_faces.add_right_click_listener(self.select_nearest_face)

        # UI elements actions
        self.tabs.currentChanged.connect(self.tab_changed)

        # UI elements actions (vertex tab)
        self.vertex_list_w.itemClicked.connect(self.item_vertex_clicked)
        self.vertex_x_w.valueChanged.connect(self.vertex_x_spinner_value_change)
        self.vertex_y_w.valueChanged.connect(self.vertex_y_spinner_value_change)
        self.delete_vertex_w.clicked.connect(self.delete_selected)

        # UI elements actions (faces tab)
        self.create_face_w.clicked.connect(self.create_face)
        self.unselect_vertex_w.clicked.connect(self.unselect_all_faces_vertex)
        self.face_list_w.itemClicked.connect(self.item_face_clicked)
        self.delete_face_w.clicked.connect(self.delete_face)
        self.display_repeated_faces_w.stateChanged.connect(self.change_repeated)

    # Menu actions
    def open_template(self):
        template_file = QtWidgets.QFileDialog.getOpenFileName(self, "Open template")
        if template_file is not None and len(template_file[0]) > 0:
            self.template = rfsu.read_template(template_file[0])
            self.unselect_all_vertex()
            self.unselect_all_faces()
            self.unselect_all_faces_vertex()
            self.update_vertex_list()
            self.update_face_list()
            self.dirty_vertex_ids = False

    def save_template(self):
        if self.dirty_vertex_ids:
            self.calculate_vertex_ids()
        template_file = QtWidgets.QFileDialog.getSaveFileName(self, "Save template")
        rfsu.write_template(template_file[0], self.template)

    def open_texture(self):
        texture_file = QtWidgets.QFileDialog.getOpenFileName(self, "Select texture")
        if texture_file is not None and len(texture_file[0]) > 0:
            self.image_viewer.load_image(texture_file[0])
            self.image_viewer_faces.load_image(texture_file[0])

    # Image viewer listeners (vertex)
    def ivv_draw_temporal_vertex(self, mouse_event):
        self.unselect_all_vertex()
        self.draw_temporal_vertex = True
        x, y = self.image_viewer.get_normalized_coords(mouse_event)
        self.temporal_vertex_pos = (x, y)
        self.image_viewer.update()

    def move_temporal_vertex(self, mouse_event):
        if self.draw_temporal_vertex:
            x, y = self.image_viewer.get_normalized_coords(mouse_event)
            self.temporal_vertex_pos = (x, y)
            self.image_viewer.update()

    def add_vertex(self, mouse_event):
        if self.draw_temporal_vertex:
            self.set_dirty_vertex_list()
            self.unselect_all_vertex()
            self.draw_temporal_vertex = False
            x, y = self.image_viewer.get_normalized_coords(mouse_event)
            self.template.vertex.append(rfsm.RFTemplateVertex(x, y))
            self.select_vertex(self.template.vertex[len(self.template.vertex) - 1])
            self.update_vertex_list()

    def cancel_vertex(self, _mouse_event):
        self.draw_temporal_vertex = False
        self.image_viewer.update()

    def select_nearest_vertex(self, mouse_event):
        self.unselect_all_vertex()
        x, y = self.image_viewer.get_normalized_coords(mouse_event)
        mouse_pos = (x, y)
        near_vertex = []
        for v in self.template.visible_vertex():
            dist = rfsu.size_vector(rfsu.sub_vectors(mouse_pos, v.coords))
            if dist < 0.01:
                near_vertex.append((v, dist))

        if len(near_vertex) > 0:
            near_vertex = sorted(near_vertex, key=lambda elem: elem[1])
            self.select_vertex(near_vertex[0][0])

    # Image viewer listeners (faces)
    def select_nearest_vertex_in_quad(self, mouse_event):
        x, y = self.image_viewer_faces.get_normalized_coords(mouse_event)
        quad = self.image_viewer_faces.get_coords_quad(mouse_event)
        mouse_pos = (x - int(x), y - int(y))
        near_vertex = []
        for v in self.template.visible_vertex():
            dist = rfsu.size_vector(rfsu.sub_vectors(mouse_pos, v.coords))
            if dist < 0.01 * self.image_viewer_faces.paint_repeated:
                near_vertex.append((v, dist))

        if len(near_vertex) > 0:
            near_vertex = sorted(near_vertex, key=lambda elem: elem[1])
            if quad >= 0:
                self.select_face_vertex(near_vertex[0][0], quad)
            self.unselect_vertex_w.setEnabled(True)
        self.image_viewer_faces.update()

    def select_nearest_face(self, mouse_event):
        x, y = self.image_viewer_faces.get_normalized_coords(mouse_event)
        self.unselect_all_faces()
        for f in self.template.faces:
            polygon = rfsu.Polygon([v.coords for v in f.vertex])
            if polygon.contains((x, y)):
                self.select_face(f)
                f.selected = True
                break
        self.image_viewer_faces.update()

    # UI elements actions
    def tab_changed(self):
        self.unselect_all_vertex()
        if self.dirty_vertex_ids:
            self.calculate_vertex_ids()
            self.unselect_all_faces()
            self.unselect_all_faces_vertex()
            self.update_face_list()
        self.image_viewer.on_canvas_change()
        self.image_viewer_faces.on_canvas_change()

    # UI elements actions (vertex)
    def vertex_image_drawer(self, painter):
        wfactor = self.image_viewer.qimage_scaled.width()
        hfactor = self.image_viewer.qimage_scaled.height()

        # Draw vertex list
        for v in self.template.visible_vertex():
            pen = QPen(QtCore.Qt.GlobalColor.blue if v.selected else QtCore.Qt.GlobalColor.red, 1)
            painter.setPen(pen)
            painter.drawEllipse(QPoint(v.coords[0] * wfactor, v.coords[1] * hfactor), 2, 2)

        # Draw temporal vertex
        if self.draw_temporal_vertex:
            pen = QPen(QtCore.Qt.GlobalColor.blue, 1)
            painter.setPen(pen)
            painter.drawEllipse(QPoint(self.temporal_vertex_pos[0] * wfactor, self.temporal_vertex_pos[1] * hfactor),
                                2, 2)

    def item_vertex_clicked(self, item):
        self.unselect_all_vertex()
        self.select_vertex(item.vertex)

    def vertex_x_spinner_value_change(self, value):
        pos = 0
        for v in self.template.visible_vertex():
            if v.selected:
                v.coords = (value, v.coords[1])
                item_in_list = self.vertex_list_w.item(pos)
                if item_in_list is not None:
                    item_in_list.setText(str(v.coords))
                self.set_dirty_vertex_list()
            pos = pos + 1
        self.image_viewer.update()

    def vertex_y_spinner_value_change(self, value):
        pos = 0
        for v in self.template.visible_vertex():
            if v.selected:
                v.coords = (v.coords[0], value)
                item_in_list = self.vertex_list_w.item(pos)
                if item_in_list is not None:
                    item_in_list.setText(str(v.coords))
                self.set_dirty_vertex_list()
            pos = pos + 1
        self.image_viewer.update()

    # UI elements actions (faces)
    def faces_image_drawer(self, painter):
        wfactor = self.image_viewer_faces.qimage_scaled.width()
        hfactor = self.image_viewer_faces.qimage_scaled.height()

        # Draw vertex list
        for v in self.template.visible_vertex():
            for i in range(0, self.image_viewer_faces.paint_repeated):
                for j in range(0, self.image_viewer_faces.paint_repeated):
                    quad = self.image_viewer_faces.get_quad(i, j)
                    is_selected = quad in v.selectedInQuads
                    pen = QPen(QtCore.Qt.GlobalColor.blue if is_selected else QtCore.Qt.GlobalColor.red, 1)
                    painter.setPen(pen)
                    painter.drawEllipse(QPoint((v.coords[0] + j) * wfactor, (v.coords[1] + i) * hfactor), 2, 2)

        def draw_triangle(triangle, color):
            brush = QBrush(color)
            brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
            painter.setBrush(brush)
            painter.drawPolygon(triangle, QtCore.Qt.FillRule.OddEvenFill)

        pen = QPen(QtCore.Qt.GlobalColor.blue, 0.3)
        painter.setPen(pen)

        col = QColor(0, 0, 255, 80)
        col_sel = QColor(255, 255, 0, 80)
        col_shadow = QColor(0, 0, 40, 50)
        col_shadow_sel = QColor(40, 20, 0, 50)
        for f in self.template.faces:
            face_pol = QPolygon([QPoint((v.coords[0] * wfactor), (v.coords[1] * hfactor)) for v in f.vertex])
            draw_triangle(face_pol, col if not f.selected else col_sel)

            # draw shadow_faces
            if self.display_repeated_faces:
                for i in [-1, 0, 1]:
                    for j in [-1, 0, 1]:
                        one_inside_all = False
                        for v in f.vertex:
                            if 0 < (v.coords[0] + j) <= 2 and 0 < (v.coords[1] + i) <= 2:
                                one_inside_all = True
                        if one_inside_all and not (i == 0 and j == 0):
                            fp_sh = QPolygon([QPoint(((v.coords[0] + j) * wfactor), ((v.coords[1] + i) * hfactor))
                                              for v in f.vertex])
                            draw_triangle(fp_sh, col_shadow if not f.selected else col_shadow_sel)

    def unselect_all_faces_vertex(self):
        for v in self.template.vertex:
            v.selectedInQuads = []
        self.image_viewer_faces.update()
        self.unselect_vertex_w.setEnabled(False)
        self.create_face_w.setEnabled(False)

    def create_face(self):
        face_vertex = self.get_selected_face_vertex()

        if len(face_vertex) == 3:
            self.unselect_all_faces()
            face = rfsm.RFTemplateFace(face_vertex[0], face_vertex[1], face_vertex[2])
            face.selected = True
            self.template.faces.append(face)
            self.unselect_all_faces_vertex()
            self.update_face_list()
            self.select_face(face)
        else:
            print("WARN: face_vertex len", len(face_vertex))

    def delete_face(self):
        self.delete_face_w.setEnabled(False)
        new_face_list = []
        for f in self.template.faces:
            if not f.selected:
                new_face_list.append(f)
        self.template.faces = new_face_list
        self.update_face_list()

    def change_repeated(self):
        self.display_repeated_faces = self.display_repeated_faces_w.isChecked()
        self.image_viewer_faces.update()

    def item_face_clicked(self, item):
        self.unselect_all_faces()
        self.select_face(item.face)

    # System events
    def resizeEvent(self, evt):
        self.image_viewer.on_canvas_change()
        self.image_viewer_faces.on_canvas_change()

    # Common actions
    def select_vertex(self, vertex):
        vertex.selected = True
        vertex.selectedInQuads = []
        self.vertex_x_w.setValue(vertex.coords[0])
        self.vertex_y_w.setValue(vertex.coords[1])
        self.delete_vertex_w.setEnabled(True)
        self.vertex_x_w.setEnabled(True)
        self.vertex_y_w.setEnabled(True)
        self.image_viewer.update()

    def select_face_vertex(self, vertex, quad):
        vertex.selectedInQuads.append(quad)
        face_vertex = self.get_selected_face_vertex()
        self.create_face_w.setEnabled(len(face_vertex) == 3)

    def unselect_all_vertex(self):
        for v in self.template.visible_vertex():
            v.selected = False
            v.selectedInQuads = []
        self.vertex_x_w.setValue(0)
        self.vertex_y_w.setValue(0)
        self.delete_vertex_w.setEnabled(False)
        self.vertex_x_w.setEnabled(False)
        self.vertex_y_w.setEnabled(False)

    def select_face(self, face):
        face.selected = True
        self.delete_face_w.setEnabled(True)
        self.image_viewer_faces.update()

    def unselect_all_faces(self):
        self.delete_face_w.setEnabled(False)
        for f in self.template.faces:
            f.selected = False

    def update_vertex_list(self):
        self.image_viewer.update()
        self.vertex_list_w.clear()
        for v in self.template.visible_vertex():
            item = QtWidgets.QListWidgetItem(str(v.coords))
            item.vertex = v
            self.vertex_list_w.addItem(item)

    def update_face_list(self):
        self.image_viewer_faces.update()
        self.face_list_w.clear()
        for f in self.template.faces:
            item = QtWidgets.QListWidgetItem(f"{f.vertex[0].ident}-{f.vertex[1].ident}-{f.vertex[2].ident}")
            item.face = f
            self.face_list_w.addItem(item)

    def delete_selected(self):
        self.set_dirty_vertex_list()
        new_vertex_list = []
        for v in self.template.visible_vertex():
            if not v.selected:
                new_vertex_list.append(v)
        self.template.vertex = new_vertex_list
        self.update_vertex_list()
        self.unselect_all_vertex()

    def calculate_vertex_ids(self):
        recalculate_faces = False
        if self.template.total_vertex_count > 0:
            recalculate_faces = True
            for v in self.template.vertex:
                v.last_ident = v.ident
        self.template.calculate_ids()
        self.dirty_vertex_ids = False
        if recalculate_faces:
            self.template.faces = []
            for f in self.last_valid_face_list:
                new_face = []
                for v_ident in f:
                    if v_ident < self.last_valid_vertex_count:
                        for v in self.template.visible_vertex():
                            if v.last_ident == v_ident:
                                new_face.append(v)
                                break
                    elif v_ident < self.last_valid_vertex_count * 2:
                        for v in self.template.visible_vertex():
                            if v.last_ident == v_ident % self.last_valid_vertex_count:
                                new_face.append(self.template.get_vertex_right(v))
                                break
                    elif v_ident < self.last_valid_vertex_count * 3:
                        for v in self.template.visible_vertex():
                            if v.last_ident == v_ident % self.last_valid_vertex_count:
                                new_face.append(self.template.get_vertex_bottom(v))
                                break
                    elif v_ident < self.last_valid_vertex_count * 4:
                        for v in self.template.visible_vertex():
                            if v.last_ident == v_ident % self.last_valid_vertex_count:
                                new_face.append(self.template.get_vertex_diag_cell(v))
                                break
                if len(new_face) == 3:
                    face = rfsm.RFTemplateFace(new_face[0], new_face[1], new_face[2])
                    face.selected = False
                    self.template.faces.append(face)

    def set_dirty_vertex_list(self):
        if not self.dirty_vertex_ids:
            self.dirty_vertex_ids = True
            self.last_valid_face_list = [[v.ident for v in f.vertex] for f in self.template.faces]
            self.last_valid_vertex_count = len(self.template.visible_vertex())
            self.template.vertex = self.template.visible_vertex()
            self.template.vertex_count = 0
            self.template.faces = []

    def get_selected_face_vertex(self):
        face_vertex = []
        for v in self.template.visible_vertex():
            for q in v.selectedInQuads:
                if q == 0:
                    face_vertex.append(v)
                elif q == 1:
                    face_vertex.append(self.template.get_vertex_right(v))
                elif q == 2:
                    face_vertex.append(self.template.get_vertex_bottom(v))
                elif q == 3:
                    face_vertex.append(self.template.get_vertex_diag_cell(v))
                else:
                    print("WARN: QUAD ", q)
        return face_vertex


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = TemplateEditor()
    app.exec_()
