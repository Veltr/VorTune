import os
import sys
import typing

from PyQt5 import QtGui
from PyQt5.QtWidgets import QMainWindow, QLabel, QScrollArea, QSizePolicy, QFileDialog, QApplication, QVBoxLayout, \
    QHBoxLayout, QPushButton, QWidget, QLineEdit, QSplitter, QTextEdit, QFrame, QErrorMessage, QCheckBox, QGridLayout
from PyQt5.QtGui import QImage, QPainter, QPixmap, QPalette, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPoint

import numpy as np
from random import randint
import graphviz

from forchun import Forchun, Forchun_Draw_Result, Beachline, Node


class Image_Area(QScrollArea):
    class Image_Label(QLabel):
        _signal : pyqtSignal

        def __init__(self, signal):
            super().__init__()
            self.setMouseTracking(True)
            self._signal = signal

        def mouseMoveEvent(self, e):
            self._signal.emit(e)

    _image_label : Image_Label

    _back_color : QColor
    _line_pen : QPen
    _complete_line_pen: QPen
    _sites_pen : QPen
    _sites_event_pen : QPen
    _circle_event_pen : QPen
    _circle_event_not_valid_pen : QPen

    _origin : QPixmap

    _mouse_signal = pyqtSignal([QtGui.QMouseEvent])
    _graph_sig : pyqtSignal

    forch : Forchun = None

    def __init__(self, size : QSize, graph_sig : pyqtSignal):
        super().__init__()
        self._graph_sig = graph_sig

        self._set_pens()

        self._mouse_signal.connect(self._mouse_move)
        self._image_label = Image_Area.Image_Label(self._mouse_signal)
        self._image_label.setBackgroundRole(QPalette.Base)
        self._image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._image_label.setScaledContents(True)

        self.setBackgroundRole(QPalette.Dark)
        self.setWidget(self._image_label)

        self.set_image(size)

    def _set_pens(self):
        self._back_color = QColor(0, 0, 0, 255)

        self._line_pen = QtGui.QPen()
        self._line_pen.setWidth(2)
        self._line_pen.setColor(QColor(255, 255, 255, 255))

        self._complete_line_pen = QtGui.QPen()
        self._complete_line_pen.setWidth(1)
        self._complete_line_pen.setColor(QColor(255, 0, 255, 255))

        self._sites_pen = QtGui.QPen()
        self._sites_pen.setWidth(10)
        self._sites_pen.setColor(QColor(255, 0, 0, 255))

        self._sites_event_pen = QtGui.QPen()
        self._sites_event_pen.setWidth(1)
        self._sites_event_pen.setColor(QColor(255, 0, 0, 255))

        self._circle_event_pen = QtGui.QPen()
        self._circle_event_pen.setWidth(1)
        self._circle_event_pen.setColor(QColor(0, 0, 255, 255))

        self._circle_event_not_valid_pen = QtGui.QPen()
        self._circle_event_not_valid_pen.setWidth(1)
        self._circle_event_not_valid_pen.setColor(QColor(128, 128, 128, 255))

    def set_image(self, size : QSize, sites : list[tuple[int, int]] = None):
        pix = QPixmap(size)
        pix.fill(self._back_color)

        if sites:
            self.forch = Forchun(sites, size.width())

            pain = QPainter(pix)
            pain.setPen(self._sites_pen)
            for s in sites: pain.drawPoint(s[0], s[1])

            pain.end()

        self._origin = pix

        self._image_label.setPixmap(pix)
        self._image_label.resize(size)

        self._update_image(-1)

    def _draw(self, to_draw : Forchun_Draw_Result, y : int):
        pix = self._origin.copy()
        size = pix.size()
        pain = QPainter(pix)

        pain.setPen(self._line_pen)
        pain.drawLine(0, y, size.width(), y)

        if to_draw.site_events:
            pain.setPen(self._sites_event_pen)
            for e in to_draw.site_events: pain.drawLine(0, e, size.width(), e)

        if to_draw.circle_events:
            for e, is_valid in to_draw.circle_events:
                if is_valid:
                    pain.setPen(self._circle_event_pen)
                else:
                    pain.setPen(self._circle_event_not_valid_pen)
                pain.drawLine(0, e, size.width(), e)

        if to_draw.completed:
            pain.setPen(self._complete_line_pen)
            for e in to_draw.completed: pain.drawLines(e)

        if to_draw.uncompleted:
            pain.setPen(self._line_pen)
            for e in to_draw.uncompleted: pain.drawLines(e)

        pain.end()
        self._image_label.setPixmap(pix)
        self._graph_sig.emit(self.forch.beachline)

    def _update_image(self, y : int):
        if not self.forch: return
        self._draw(self.forch.draw_by(y), y)

    def draw_next(self):
        if not self.forch: return
        self.forch.next_step()
        self._draw(self.forch.draw_current(), self.forch.cur_d)

    def draw_prev(self):
        if not self.forch: return
        self._draw(self.forch.draw_by_prev_step(), self.forch.cur_d)

    def draw_all(self):
        if not self.forch: return
        self.forch.all_steps()
        self.forch.cur_d += self.height()
        self._draw(self.forch.draw_current(), self.forch.cur_d)
        self.forch.cur_d -= self.height()

    def _mouse_move(self, e):
        self._update_image(e.y())

class Graph_Frame(QFrame):
    _img_l : QLabel
    _check_b : QCheckBox

    def __init__(self, signal : pyqtSignal):
        super().__init__()
        signal.connect(self.update_graph)

        v1 = QVBoxLayout()

        self._check_b = QCheckBox('Enable graphs ( high performance drop(( )')

        self._img_l = QLabel()
        self._img_l.setBackgroundRole(QPalette.Base)
        self._img_l.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._img_l.setScaledContents(True)

        self._draw_flat()

        v1.addWidget(self._check_b)
        v1.addWidget(self._img_l)

        self.setLayout(v1)
        self.setFrameShape(QFrame.Box)

    def _draw_flat(self):
        pix = QPixmap(500, 10)
        pix.fill(Qt.white)
        self._img_l.setPixmap(pix)

    def update_graph(self, tree : Beachline):
        if not self._check_b.isChecked(): return

        if not tree.root:
            self._draw_flat()
            return
        dot = graphviz.Digraph()

        def _dive(node : Node, dot : graphviz.Digraph, par_name : str = None):
            if node.type & 1: cur = f'Arc {node.id}'
            else:
                if node.edge.grow_right: cur = f'Edge R {node.id}'
                else: cur = f'Edge L {node.id}'

            dot.node(cur)
            if par_name: dot.edge(par_name, cur, arrowhead='none')

            if node.left_node: _dive(node.left_node, dot, cur)
            if node.right_node: _dive(node.right_node, dot, cur)

        file_name = '__render'
        _dive(tree.root, dot)
        # print(dot.source)
        dot.format = 'png'
        dot.render(file_name)

        self._img_l.setPixmap(QPixmap.fromImage(QImage(f'{file_name}.png')))

        os.remove(file_name)
        os.remove(f'{file_name}.png')


class Main_Window(QMainWindow):
    _img : Image_Area

    _width_l : QLineEdit
    _height_l : QLineEdit
    _site_count_l : QLineEdit

    _img_splitter: QSplitter
    _graph_sig = pyqtSignal([Beachline])

    _tb : QTextEdit
    _sites : list[tuple[int, int]]
    _triggers : int
    
    def __init__(self):
        super().__init__()

        self.setGeometry(150, 150, 1500, 750)
        self.setWindowTitle('Forchun')
        self._triggers = 0
        self.build_face()

    def build_face(self):
        sp = QSplitter(Qt.Orientation.Horizontal)
        sp.setHandleWidth(5)

        v1 = QVBoxLayout()
        self._img = Image_Area(QSize(800, 600), self._graph_sig)

        g1 = QGridLayout()
        b1 = QPushButton('Next')
        b1.clicked.connect(lambda *args: self._img.draw_next())
        b2 = QPushButton('All')
        b2.clicked.connect(lambda *args: self._img.draw_all())
        b3 = QPushButton('Previous')
        b3.clicked.connect(lambda *args: self._img.draw_prev())
        g1.addWidget(b3, 0, 0)
        g1.addWidget(b1, 0, 1)
        g1.addWidget(b2, 1, 0, 2, 2)

        v1.addWidget(self._img)
        v1.addLayout(g1)

        f1 = QFrame()
        f1.setFrameShape(QFrame.Box)
        f1.setLayout(v1)

        self._img_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._img_splitter.setHandleWidth(5)

        self._img_splitter.addWidget(Graph_Frame(self._graph_sig))
        self._img_splitter.addWidget(f1)

        self._img_splitter.setStretchFactor(0, 2)
        self._img_splitter.setStretchFactor(1, 10)

        sp.addWidget(self._img_splitter)


        def __set_trigger(n):
            self._triggers |= 1 << n

        v2 = QVBoxLayout()

        b3 = QPushButton('Update')
        b3.clicked.connect(self._update_all)

        b4 = QPushButton('Randomize')
        b4.clicked.connect(self._randomize)

        h2 = QHBoxLayout()
        self._width_l = QLineEdit('800')
        self._width_l.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._width_l.textChanged.connect(lambda *args: __set_trigger(1))
        l1 = QLabel('x')
        self._height_l = QLineEdit('600')
        self._height_l.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._height_l.textChanged.connect(lambda *args: __set_trigger(1))
        h2.addWidget(self._width_l)
        h2.addWidget(l1)
        h2.addWidget(self._height_l)

        h3 = QHBoxLayout()
        self._site_count_l = QLineEdit('10')
        self._site_count_l.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._site_count_l.textChanged.connect(lambda *args: __set_trigger(2))
        l2 = QLabel('sites')
        l2.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        h3.addWidget(self._site_count_l)
        h3.addWidget(l2)

        self._tb = QTextEdit()
        ff = QFont()
        ff.setPointSize(12)
        self._tb.setFont(ff)
        self._tb.textChanged.connect(lambda *args: __set_trigger(0))

        v2.addWidget(QLabel('Sites (x, y)'))
        v2.addWidget(self._tb)
        v2.addWidget(b4)
        v2.addLayout(h2)
        v2.addLayout(h3)
        v2.addWidget(b3)

        f2 = QFrame()
        f2.setFrameShape(QFrame.Box)
        f2.setLayout(v2)
        sp.addWidget(f2)

        sp.setStretchFactor(0, 50)
        sp.setStretchFactor(1, 20)

        self.setCentralWidget(sp)

    def __update_text(self, a):
        t = ''
        for s in a: t += f'{s[0]} {s[1]}\n'
        self._tb.setText(t)

    def __generate_sites(self):
        count = len(self._sites)
        n = int(self._site_count_l.text())

        if n < count: self._sites = self._sites[:n]
        elif n > count:
            w = int(self._width_l.text())
            h = int(self._height_l.text())

            for _ in range(n - count): self._sites.append((randint(0, w), randint(0, h)))

        self._sites.sort(key=lambda e: e[0])
        self._sites.sort(key=lambda e: e[1])

    def _randomize(self):
        self._sites = []

        self.__generate_sites()
        self.__update_text(self._sites)

    def _update_sites(self):
        a = []
        t = self._tb.toPlainText().splitlines()

        try:
            for line in t:
                sp = line.split(' ')
                x = int(sp[0])
                y = int(sp[1])
                a.append((x, y))

        except Exception as e:
            d = QErrorMessage()
            d.showMessage(str(e))
            d.exec()
            return

        self._sites = a
        self.__generate_sites()
        self.__update_text(self._sites)

    def _update_all(self):
        if self._triggers & 1: self._update_sites()
        if self._triggers & 0b100: self.__generate_sites()

        self._img.set_image(QSize(int(self._width_l.text()), int(self._height_l.text())), self._sites)
        self._triggers = 0


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Main_Window()
    window.show()
    app.exec()


