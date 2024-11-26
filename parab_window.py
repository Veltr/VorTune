import sys
import typing

from PyQt5 import QtGui
from PyQt5.QtWidgets import QMainWindow, QLabel, QScrollArea, QSizePolicy, QFileDialog, QApplication
from PyQt5.QtGui import QImage, QPainter, QPixmap, QPalette, QPen, QColor
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPoint

import numpy as np

from forchun_entities import OldParabola, Site


class Image_Label(QLabel):
    _origin : QPixmap
    _par : OldParabola

    def __init__(self, pix : QPixmap, par : OldParabola):
        super().__init__()
        self.setMouseTracking(True)

        pain = QPainter(pix)
        pen = QtGui.QPen()
        pen.setWidth(10)
        pen.setColor(QColor(255, 0, 0, 255))
        pain.setPen(pen)
        pain.drawPoint(QPoint(par.x(), par.y()))

        self._par = par
        self._origin = pix
        self.setPixmap(pix)

    def update_image(self, y : int):
        pix = self._origin.copy()
        pain = QPainter(pix)
        pen = QtGui.QPen()
        pen.setWidth(1)
        pen.setColor(QColor(255, 255, 255, 255))
        pain.setPen(pen)

        size = pix.size()
        pain.drawLine(0, y, size.width(), y)

        pen2 = QtGui.QPen()
        pen2.setWidth(1)
        pen2.setColor(QColor(0, 255, 0, 255))
        pain.setPen(pen2)
        pain.drawLines(self._par.get_points(y, range(0, size.width())))

        pain.end()
        self.setPixmap(pix)


    def mouseMoveEvent(self, e):
        self.update_image(e.y())


class Parabola_Window(QMainWindow):
    _image_label: Image_Label

    # _img_signal = pyqtSignal([QPixmap])

    def __init__(self, size: QSize):
        super().__init__()
        # self._img_signal.connect(self._image_label.setPixmap)
        pix = QPixmap(size)
        pix.fill(QColor(0, 0, 0, 255))
        self._image_label = Image_Label(pix, OldParabola(Site((400, 300))))
        self.setCentralWidget(self._image_label)




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Parabola_Window(QSize(800, 600))
    window.show()
    app.exec()




