from typing import Tuple, List, Set
from element import Element

from board._element_groups import _ELEMENT_GROUPS


class Mixin:

    def is_at(self, x, y, element_object: Element):
        return element_object in self.get_at(x, y)

    def get_at(self, x: int, y: int) -> List[Element]:
        """ Element on 3 layers of board """

        _strpos = self._xy2strpos(x, y)
        _elements = []
        for i in range(len(self._board)):
            _elements.append(Element(self._board[i][_strpos]))
        return _elements

    def get_hero(self) -> Tuple[int, int]:
        """ return hero coordiantes """

        elements = _ELEMENT_GROUPS["ROBO"]
        elements += _ELEMENT_GROUPS["ROBO_DEAD"]
        points = self._find_all([Element(el) for el in elements])
        assert len(points) <= 1, "There should be only one robo"
        return points[0]

    def get_other_heroes(self):
        elements = _ELEMENT_GROUPS["ROBO_OTHER"]\
                    + _ELEMENT_GROUPS["ROBO_OTHER_DEAD"]
        points = self._find_all([Element(el) for el in elements])
        return points

    def get_other_live_heroes(self):
        elements = _ELEMENT_GROUPS["ROBO_OTHER"]
        points = self._find_all([Element(el) for el in elements])
        return points

    def get_other_dead_heroes(self):
        """ search for corps far from starts, maybe they have gold """

        starts = set(self._find_all([Element("START")]))
        elements = _ELEMENT_GROUPS["ROBO_OTHER_DEAD"]
        points = set(self._find_all([Element(el) for el in elements]))
        points = list(points - starts)
        return points

    def get_zombies(self):
        elements = _ELEMENT_GROUPS["ZOMBIE"]
        points = self._find_all([Element(el) for el in elements])
        return points

    def get_laser_machines(self):
        elements = _ELEMENT_GROUPS["LASER_MACHINES"]
        points = self._find_all([Element(el) for el in elements])
        return points

    def get_lasers(self):
        elements = _ELEMENT_GROUPS["LASERS"]
        points = self._find_all([Element(el) for el in elements])
        return points

    def get_boxes(self):
        return self._find_all([Element("BOX")])

    def get_floors(self):
        return self._find_all([Element("FLOOR")])

    def get_holes(self):
        return self._find_all([Element("HOLE")])

    def get_exits(self):
        return self._find_all([Element("EXIT")])

    def get_starts(self):
        return self._find_all([Element("START")])

    def get_zombie_starts(self):
        return self._find_all([Element("ZOMBIE_START")])

    def get_golds(self):
        return self._find_all([Element("GOLD")])

    def get_walls(self):
        elements = _ELEMENT_GROUPS["WALLS"]
        points = self._find_all([Element(el) for el in elements])
        return points

    def get_perks(self):
        elements = _ELEMENT_GROUPS["PERKS"]
        points = self._find_all([Element(el) for el in elements])
        return points
