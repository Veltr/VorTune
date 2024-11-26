import numpy as np
import heapq as hq
from queue import PriorityQueue

from forchun_entities import *

class Forchun_Draw_Result:
    site_events : list[int]
    circle_events : list[int, bool]  # y, is_valid

    completed : list[QPolygon]
    uncompleted : list[QPolygon]

    def __init__(self, site_events : list[int], circle_events : list[int, bool],
                 completed : list[QPolygon], uncompleted : list[QPolygon]):
        self.site_events = site_events
        self.circle_events = circle_events
        self.completed = completed
        self.uncompleted = uncompleted

class Node:
    type : int = 0  # 1 - parabola, 0b10 - edge
    id : int  # graph staff only

    edge : Edge = None
    par : Parabola = None

    left_node = None
    right_node = None
    parent = None

    def __init__(self, e : FEntity, id):
        self.set_entity(e)
        self.id = id

    def set_left(self, node):
        self.left_node = node
        self.left_node.parent = self

    def set_right(self, node):
        self.right_node = node
        self.right_node.parent = self

    def set_entity(self, e : FEntity):
        if isinstance(e, Edge):
            self.edge = e
            self.type = 2
        else:
            self.par = e
            self.type = 1

    def get_entity(self):
        if self.type & 1: return self.par
        return self.edge

    def get_left_leaf(self):
        if not self.left_node: return None

        node = self.left_node
        while node.right_node: node = node.right_node
        return node

    def get_right_leaf(self):
        if not self.right_node: return None

        node = self.right_node
        while node.left_node: node = node.left_node
        return node

    def get_left_parent_edge(self):
        node = self
        while node.parent and node.parent.left_node == node: node = node.parent
        return node.parent

    def get_right_parent_edge(self):
        node = self
        while node.parent and node.parent.right_node == node: node = node.parent
        return node.parent



class Beachline:
    root : Node = None
    node_counter = 0  # graph purpose only

    def get_parabola_by_x(self, x : int, d : int):
        cur_node = self.root
        while not (cur_node.type & 1):
            left = cur_node.get_left_leaf()
            right = cur_node.get_right_leaf()

            parent_edge_node : Edge = left.get_right_parent_edge().edge
            left_inter = parent_edge_node.get_intersection_with_parabola(left.par, d)
            right_inter = parent_edge_node.get_intersection_with_parabola(right.par, d)

            if not left_inter and right_inter: inter_x = right_inter[0]
            else: inter_x = left_inter[0]

            if x < inter_x: cur_node = cur_node.left_node
            else: cur_node = cur_node.right_node

        return cur_node

    def set_parent_from_node(self, from_node : Node, to_node : Node):
        if from_node.parent:
            if from_node.parent.left_node == from_node: from_node.parent.set_left(to_node)
            else: from_node.parent.set_right(to_node)
        else: self.root = to_node

class Forchun:
    sites : list[Site]
    _complete_edges : list[tuple[tuple[int, int], tuple[int, int]]]  # (start, finish)
    _width : int
    beachline : Beachline
    # beachline : list[tuple[int, int, Parabola]]  # from x1 inclusive to x2 exclusive lays par

    _events_q : PriorityQueue  # y, Event

    cur_d : int = -1

    def __init__(self, sites : list[tuple[int, int]], width : int):
        self.sites = []
        self._width = width
        self._events_q = PriorityQueue()
        # self.beachline = Beachline(self._events_q, width)
        # self.beachline = []
        self.beachline = Beachline()
        self._states = []
        self._complete_edges = []

        for s in sites:
            s0 = Site(s)
            self.sites.append(s0)
            self._events_q.put((s0.y(), Site_Event(s0)))

    def next_step(self):
        if self._events_q.empty(): return

        y, e = self._events_q.get_nowait()
        if e.type & 1: self._site_event(e.site)
        elif e.is_valid: self._circle_event(e)

        self.cur_d = y

    def next_stop_by(self, y : int):
        while y > self.cur_d:
            if self._events_q.empty() or self._events_q.queue[0][0] >= y: break
            self.next_step()

    def all_steps(self):
        if self._events_q.empty(): return

        while not self._events_q.empty():
            y, e = self._events_q.get_nowait()
            if e.type & 1: self._site_event(e.site)
            elif e.is_valid: self._circle_event(e)

            self.cur_d = y

    def draw(self, d : int):
        site_events = []
        circle_events = []
        completed = []
        uncompleted = []

        for ey, e in self._events_q.queue:
            if e.type & 1: site_events.append(ey)
            else: circle_events.append((ey, e.is_valid))

        def _dive(node : Node):
            min_x, max_x = 0., self._width

            if node.type & 1:
                par = node.par
                # print(d)
                if d == par.y():
                    uncompleted.append(par.get_points(d, None))
                else:
                    left_parent_node = node.get_left_parent_edge()
                    right_parent_node = node.get_right_parent_edge()

                    if left_parent_node:
                        inter = left_parent_node.edge.get_intersection_with_parabola(par, d)
                        if inter: min_x = np.clip(inter[0], 0, self._width)

                    if right_parent_node:
                        inter = right_parent_node.edge.get_intersection_with_parabola(par, d)
                        if inter: max_x = np.clip(inter[0], 0, self._width)

                    uncompleted.append(par.get_points(d, range(int(min_x), int(max_x))))

            else:
                left_par = node.get_left_leaf()
                right_par = node.get_right_leaf()
                edge = node.edge
                max_y = edge.y()

                if left_par:
                    inter = edge.get_intersection_with_parabola(left_par.par, d)
                    if inter: min_x = inter[0]

                if right_par:
                    inter = edge.get_intersection_with_parabola(right_par.par, d)
                    if inter: max_x, max_y = inter[0], max(max_y, inter[1])

                if edge.grow_right:
                    uncompleted.append(edge.get_points(int(np.round(edge.x())), int(np.round(max_x)), max_y, self._width))
                else:
                    uncompleted.append(edge.get_points(int(np.round(min_x)), int(np.round(edge.x())), max_y, self._width))

            if node.left_node: _dive(node.left_node)
            if node.right_node: _dive(node.right_node)


        if self.beachline.root: _dive(self.beachline.root)

        for e in self._complete_edges:
            p = QPolygon()
            p.append(QPoint(e[0][0], e[0][1]))
            p.append(QPoint(e[1][0], e[1][1]))
            completed.append(p)

        return Forchun_Draw_Result(site_events, circle_events, completed, uncompleted)

    def draw_current(self):
        return self.draw(self.cur_d)

    def draw_by(self, y : int):
        if y <= self.cur_d: self._start_over()

        self.next_stop_by(y)
        return self.draw(y)

    def draw_by_prev_step(self):
        y = self.cur_d
        self._start_over()
        while y > self._events_q.queue[0][0]: self.next_step()
        return self.draw_current()

    def _start_over(self):
        self.cur_d = -1
        self.beachline = Beachline()
        self._states = []
        self._complete_edges = []
        self._events_q = PriorityQueue()

        for s in self.sites: self._events_q.put((s.y(), Site_Event(s)))

    def _site_event(self, site : Site):
        if not self.beachline.root:
            self.beachline.root = Node(Parabola(site), self.beachline.node_counter)
            self.beachline.node_counter += 1

            while not self._events_q.empty() and self._events_q.queue[0][0] == site.y():
                _, e = self._events_q.get_nowait()
                new_par_node = Node(Parabola(e.site), self.beachline.node_counter)
                self.beachline.node_counter += 1

                par_node = self.beachline.get_parabola_by_x(e.site.x(), site.y())
                par = par_node.par
                edge_start = ((e.site.x() + par.x()) / 2, e.site.y() - self._width)
                new_edge_node = Node(Edge(edge_start, np.inf, edge_start[0], True), 1)
                self.beachline.node_counter += 1

                self.beachline.set_parent_from_node(par_node, new_edge_node)
                if e.site.x() < par.x():
                    new_edge_node.set_left(new_par_node)
                    new_edge_node.set_right(par_node)
                else:
                    new_edge_node.set_left(par_node)
                    new_edge_node.set_right(new_par_node)

            return

        replace_par_node = self.beachline.get_parabola_by_x(site.x(), site.y())
        repl_par = replace_par_node.par

        y = repl_par.get_point(site.y(), site.x())

        # k = (2 * (site.x() - repl_par.x())) / (repl_par.y() - site.y())
        k = (site.x() - repl_par.x()) / (repl_par.y() - site.y())
        b = y - k * site.x()
        # edge_left_node = Node(Edge(site.pos, k, b, False))
        # edge_right_node = Node(Edge(site.pos, k, b, True))
        edge_left_node = Node(Edge((site.x(), y), k, b, False), self.beachline.node_counter)
        edge_right_node = Node(Edge((site.x(), y), k, b, True), self.beachline.node_counter + 1)
        self.beachline.node_counter += 2

        repl_par_left_node = Node(Parabola(repl_par.site), self.beachline.node_counter)
        repl_par_right_node = Node(Parabola(repl_par.site), self.beachline.node_counter + 1)
        new_par_node = Node(Parabola(site), self.beachline.node_counter + 2)
        self.beachline.node_counter += 3

        self.beachline.set_parent_from_node(replace_par_node, edge_left_node)

        edge_left_node.set_left(repl_par_left_node)
        edge_left_node.set_right(edge_right_node)

        edge_right_node.set_left(new_par_node)
        edge_right_node.set_right(repl_par_right_node)

        if repl_par.circle_event: repl_par.circle_event.is_valid = False

        self._add_circle_event(repl_par_left_node)
        self._add_circle_event(repl_par_right_node)


    def _add_circle_event(self, par_node : Node):
        par = par_node.par

        left_edge_node = par_node.get_left_parent_edge()
        right_edge_node = par_node.get_right_parent_edge()

        if not left_edge_node or not right_edge_node: return

        inter = left_edge_node.edge.get_intersection_with_edge(right_edge_node.edge)
        if not inter: return

        offset_x, offset_y = par.x() - inter[0], par.y() - inter[1]
        event_y = int(np.round(inter[1] + np.sqrt(offset_x * offset_x + offset_y * offset_y)))

        if par.circle_event:
            # if par.circle_event.d >= event_y: return
            # if par.circle_event.d < event_y: return
            par.circle_event.is_valid = False

        e = Circle_Event(event_y, inter, par_node)
        self._events_q.put((e.d, e))
        par.circle_event = e


    def _circle_event(self, e : Circle_Event):
        left_edge_node = e.par_node.get_left_parent_edge()
        right_edge_node = e.par_node.get_right_parent_edge()

        left_par_node = left_edge_node.get_left_leaf()
        right_par_node = right_edge_node.get_right_leaf()

        self._complete_edges.append((left_edge_node.edge.point_int(), e.point_int()))
        self._complete_edges.append((e.point_int(), right_edge_node.edge.point_int()))

        try:
            k = (right_par_node.par.x() - left_par_node.par.x()) / (left_par_node.par.y() - right_par_node.par.y())
            b = e.inter_point[1] - k * e.inter_point[0]
        except:
            k = np.inf
            b = e.inter_point[0]

        new_edge = Edge(e.inter_point, k, b, left_edge_node.edge.grow_right if
        left_edge_node.edge.grow_right == right_edge_node.edge.grow_right else k >= 0)
        new_edge_node = Node(new_edge, self.beachline.node_counter)
        self.beachline.node_counter += 1

        high_edge : Node = None
        node = e.par_node
        while node.parent:
            node = node.parent
            if node == left_edge_node: high_edge = left_edge_node
            if node == right_edge_node: high_edge = right_edge_node

        self.beachline.set_parent_from_node(high_edge, new_edge_node)

        new_edge_node.set_left(high_edge.left_node)
        new_edge_node.set_right(high_edge.right_node)

        parent = e.par_node.parent
        if parent.left_node == e.par_node: remain_node = parent.right_node
        else: remain_node = parent.left_node

        self.beachline.set_parent_from_node(parent, remain_node)

        if e.par_node.par.circle_event: e.par_node.par.circle_event.is_valid = False
        self._add_circle_event(left_par_node)
        self._add_circle_event(right_par_node)

