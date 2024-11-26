import typing
from abc import abstractmethod
import numpy as np
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPolygon

# from forchun import Node


class FEntity:
    @abstractmethod
    def x(self): pass

    @abstractmethod
    def y(self): pass

    def point(self): return self.x(), self.y()

    def point_int(self): return int(np.round(self.x())), int(np.round(self.y()))

    # def get_points(self, d : int, x_range : typing.Iterable[int]): pass


class Site(FEntity):
    pos : tuple[int, int]

    def __init__(self, pos : tuple[int, int]):
        self.pos = pos

    def x(self): return self.pos[0]
    def y(self): return self.pos[1]

    def __copy__(self):
        return Site((self.x(), self.y()))

class FEvent(FEntity):
    type: int  # 1 - site, 0b10 - intersection

    @abstractmethod
    def x(self): pass

    @abstractmethod
    def y(self): pass

    def __lt__(self, other):
        if isinstance(self, Site_Event):
            if isinstance(other, Site_Event): return self.x() > other.x()
            return True
        else:
            if isinstance(other, Site_Event): return False
            return self.x() > other.x()


class Site_Event(FEvent):
    site: Site

    def __init__(self, site: Site):
        self.type = 1
        self.site = site

    def x(self): return self.site.x()
    def y(self): return self.site.y()

class Circle_Event(FEvent):
    d : int
    inter_point : tuple[float, float]
    is_valid = True
    par_node = None  # Node

    def __init__(self, d : int, inter_point : tuple[int, int], par_node):
        self.type = 0b10
        self.d = d
        self.inter_point = inter_point
        self.par_node = par_node


    def x(self): return self.inter_point[0]

    def y(self): return self.inter_point[1]

class Parabola(FEntity):
    site : Site
    circle_event : Circle_Event = None

    def __init__(self, site : Site):
        self.site = site

    def x(self): return self.site.x()
    def y(self): return self.site.y()

    def get_point(self, d : int, x : int):
        return np.pow(x - self.x(), 2) / (2. * (self.y() - d)) + (d + self.y()) / 2.

    def get_point_int(self, d : int, x : int):
        return int(np.round(self.get_point(d, x)))

    def get_points(self, d : int, x_range : typing.Iterable[int]):
        out = QPolygon()
        x0, y0 = self.x(), self.y()

        if d == y0:
            for i in range(1000): out.append(QPoint(x0, d - i))
        else:
            for i, x in enumerate(x_range):
                out.append(QPoint(x, self.get_point_int(d, x)))

        return out

    # y = a * x^2 + b * x0 + c
    def to_normal_form(self, d : int):
        x, y = self.x(), self.y()

        a = 1. / (2. * (y - d))
        t = 2. * a * x
        return a, -t, (d + y + t * x) / 2.

    # def __lt__(self, other):
    #     if self.x() != other.x(): return self.x() > other.x()
    #     if self.y() != other.y(): return self.y() > other.y()
    #
    #     return True

class Edge(FEntity):
    _start : tuple[float, float]
    grow_right : bool

    k : float
    b : float

    def __init__(self, start : tuple[float, float], k : float, b : float, grow_right : bool):
        self._start = start
        self.grow_right = grow_right

        if k == -0.: self.k = 0.
        else: self.k = k
        self.b = b

    def x(self): return self._start[0]

    def y(self): return self._start[1]

    def get_intersection_with_parabola(self, par : Parabola, d : int) -> tuple[float, float]:
        if self.k == np.inf:
            if d == par.y():
                if self.x() == par.x(): return par.x(), par.y()
                else: return None

            return self.x(), par.get_point(d, int(self.x()))

        if par.y() == d:
            if (self.grow_right and par.x() >= self.x()) or (not self.grow_right and par.x() <= self.x()):
                return par.x(), self.k * par.x() + self.b
            else: return None

        a, b, c = par.to_normal_form(d)

        b1 = b - self.k
        c1 = c - self.b

        dis = b1 * b1 - 4 * a * c1
        if dis < 0.: return None
        x1, x2 = (-b1 + np.sqrt(dis)) / (2. * a), (-b1 - np.sqrt(dis)) / (2. * a)

        if self.grow_right:
            x = max(x1, x2)
            if x < self.x(): return None
        else:
            x = min(x1, x2)
            if x > self.x(): return None

        return x, self.k * x + self.b

    def get_intersection_with_edge(self, edge):
        if self.k == edge.k: return None

        if self.k == np.inf: x = self.b
        elif edge.k == np.inf: x = edge.b
        else: x = (edge.b - self.b) / (self.k - edge.k)

        if (self.grow_right and x < self.x()) or (not self.grow_right and x > self.x()) or \
                (edge.grow_right and x < edge.x()) or (not edge.grow_right and x > edge.x()): return None

        return x, self.get_point(x) if edge.k == np.inf else edge.get_point(x)


    def get_point(self, x : float):
        return self.k * x + self.b

    def get_point_int(self, x : int):
        return int(np.round(self.get_point(x)))

    def get_points(self, x1 : int, x2 : int, max_y : int, max_x : int):
        out = QPolygon()
        if self.k == np.inf:
            out.append(QPoint(int(np.round(self.x())), int(np.round(self.y()))))
            out.append(QPoint(int(np.round(self.x())), int(np.round(max_y))))
        else:
            x1, x2 = int(np.clip(x1, 0, max_x)), int(np.clip(x2, 0, max_x))
            out.append(QPoint(x1, self.get_point_int(x1)))
            out.append(QPoint(x2, self.get_point_int(x2)))
        return out


