from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
from PyQt5 import QtCore, QtWidgets


class ImageViewer:
    """
    Basic image viewer class to show an image with zoom and pan functionaities.
    Requirement: Qt's Qlabel widget name where the image will be drawn/displayed.
    """

    def __init__(self, qlabel):
        self.qlabel_image = qlabel
        self.qimage_scaled = QImage()
        self.qpixmap = QPixmap()
        self.qimage = None
        self.zoomX = 1
        self.position = [0, 0]

        self.qlabel_image.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.__connect_events()

        self.left_click_listeners = []
        self.left_release_listeners = []
        self.right_click_listeners = []
        self.move_listeners = []
        self.over_image_drawer = []

        self.has_image = False
        self.paint_repeated = 1  # Draws the image repeated paint_repeated x paint_repeated

    def __connect_events(self):
        # Mouse events
        self.qlabel_image.mousePressEvent = self.mouse_press_action
        self.qlabel_image.mouseMoveEvent = self.mouse_move_action
        self.qlabel_image.mouseReleaseEvent = self.mouse_release_action

    def on_canvas_change(self):
        if self.has_image:
            self.qpixmap = QPixmap(self.qlabel_image.size())
            self.qpixmap.fill(QtCore.Qt.GlobalColor.gray)
            self.qimage_scaled = self.qimage.scaled(self.qlabel_image.width() * self.zoomX, self.qlabel_image.height() *
                                                    self.zoomX, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
            self.qimage_scaled = self.qimage_scaled.scaled(int(self.qimage_scaled.width() / self.paint_repeated),
                                                           int(self.qimage_scaled.height() / self.paint_repeated),
                                                           QtCore.Qt.AspectRatioMode.KeepAspectRatio)
            self.update()

    def load_image(self, image_path):
        self.qimage = QImage(image_path)
        self.qpixmap = QPixmap(self.qlabel_image.size())
        if not self.qimage.isNull():
            # reset Zoom factor and Pan position
            self.zoomX = 1
            self.position = [0, 0]
            self.qimage_scaled = self.qimage.scaled(self.qlabel_image.width(), self.qlabel_image.height(),
                                                    QtCore.Qt.AspectRatioMode.KeepAspectRatio)
            self.qimage_scaled = self.qimage_scaled.scaled(int(self.qimage_scaled.width() / self.paint_repeated),
                                                           int(self.qimage_scaled.height() / self.paint_repeated),
                                                           QtCore.Qt.AspectRatioMode.KeepAspectRatio)
            self.update()
            self.has_image = True
        else:
            self.statusbar.showMessage('Cannot open this image! Try another one.', 5000)

    def update(self):
        if not self.qimage_scaled.isNull():
            # check if position is within limits to prevent unbounded panning.
            px, py = self.position
            px = px if (px <= self.qimage_scaled.width() - self.qlabel_image.width()) \
                else (self.qimage_scaled.width() - self.qlabel_image.width())
            py = py if (py <= self.qimage_scaled.height() - self.qlabel_image.height()) \
                else (self.qimage_scaled.height() - self.qlabel_image.height())
            px = px if (px >= 0) else 0
            py = py if (py >= 0) else 0
            self.position = (px, py)

            if self.zoomX == 1:
                self.qpixmap.fill(QtCore.Qt.GlobalColor.white)

            # the act of painting the qpixamp
            painter = QPainter()
            painter.begin(self.qpixmap)
            for i in range(0, self.paint_repeated):
                for j in range(0, self.paint_repeated):
                    rect = QtCore.QRect(self.position[0], self.position[1],
                                        self.qlabel_image.width(), self.qlabel_image.height())
                    painter.drawImage(QtCore.QPoint(self.qimage_scaled.width() * i, self.qimage_scaled.height() * j),
                                      self.qimage_scaled, rect)

                    # separation lines
                    pen = QPen(QtCore.Qt.GlobalColor.white, 3)
                    painter.setPen(pen)
                    if i < self.paint_repeated - 1:
                        painter.drawLine(self.qimage_scaled.width() * (i+1), self.qimage_scaled.height() * j,
                                         self.qimage_scaled.width() * (i+1), self.qimage_scaled.height() * (j+1))
                    if j < self.paint_repeated - 1:
                        painter.drawLine(self.qimage_scaled.width() * i, self.qimage_scaled.height() * (j+1),
                                         self.qimage_scaled.width() * (i+1), self.qimage_scaled.height() * (j+1))

            # Image drawers
            for drawer in self.over_image_drawer:
                drawer(painter)

            painter.end()

            self.qlabel_image.setPixmap(self.qpixmap)
        else:
            pass

    def mouse_press_action(self, mouse_event):
        if mouse_event.button() == QtCore.Qt.MouseButton.LeftButton and self.has_image:
            for click_listener in self.left_click_listeners:
                click_listener(mouse_event)

        if mouse_event.button() == QtCore.Qt.MouseButton.RightButton and self.has_image:
            for click_listener in self.right_click_listeners:
                click_listener(mouse_event)

    def mouse_move_action(self, mouse_event):
        if self.has_image:
            for click_listener in self.move_listeners:
                click_listener(mouse_event)

    def mouse_release_action(self, mouse_event):
        if mouse_event.button() == QtCore.Qt.MouseButton.LeftButton and self.has_image:
            for click_listener in self.left_release_listeners:
                click_listener(mouse_event)

    def add_left_click_listener(self, listener):
        self.left_click_listeners.append(listener)

    def add_move_listener(self, listener):
        self.move_listeners.append(listener)

    def add_left_release_listener(self, listener):
        self.left_release_listeners.append(listener)

    def add_right_click_listener(self, listener):
        self.right_click_listeners.append(listener)

    def add_over_image_drawer(self, drawer):
        self.over_image_drawer.append(drawer)

    def get_normalized_coords(self, mouse_event):
        mx, my = mouse_event.pos().x(), mouse_event.pos().y()
        x = mx / self.qimage_scaled.width()
        y = my / self.qimage_scaled.height()
        x = x if x < self.paint_repeated else self.paint_repeated
        y = y if y < self.paint_repeated else self.paint_repeated
        x = x if x > 0 else 0
        y = y if y > 0 else 0
        return x, y

    def get_coords_quad(self, mouse_event):
        mx, my = mouse_event.pos().x(), mouse_event.pos().y()
        quad = -1
        for i in range(0, self.paint_repeated):
            for j in range(0, self.paint_repeated):
                win = j * self.qimage_scaled.width() <= mx < (j + 1) * self.qimage_scaled.width()
                hin = i * self.qimage_scaled.height() <= my < (i + 1) * self.qimage_scaled.height()
                if win and hin:
                    quad = self.get_quad(i, j)
        return quad

    def get_quad(self, i, j):
        return i * self.paint_repeated + j
