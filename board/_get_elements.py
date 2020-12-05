from typing import Tuple, List, Set
from element import Element


class Mixin:
    
    def get_at(self, x: int, y: int) -> List[Element]:
        """ Element on 3 layers of board """
        
        _strpos = self._xy2strpos(x, y)
        _elements = []
        for i in range(len(self._board)):
            _elements.append(Element(self._board[i][_strpos]))
        return _elements
    
    def get_hero(self) -> Tuple[int, int]:
        """ return hero coordiantes """
        
        points = set()
        points.update(self._find_all(Element('ROBO_FALLING')))
        points.update(self._find_all(Element('ROBO_LASER')))
        points.update(self._find_all(Element('ROBO')))
        points.update(self._find_all(Element('ROBO_FLYING')))
        assert len(points) <= 1, "There should be only one robo"
        return list(points)[0]

    def get_other_heroes(self):
        points = set()
        points.update(self._find_all(Element('ROBO_OTHER_FALLING')))
        points.update(self._find_all(Element('ROBO_OTHER_LASER')))
        points.update(self._find_all(Element('ROBO_OTHER')))
        points.update(self._find_all(Element('ROBO_OTHER_FLYING')))
        return list(points)

    def get_empty(self):
        return self._find_all(Element('EMPTY'))

    def get_zombies(self):
        points = set()
        points.update(self._find_all(Element('FEMALE_ZOMBIE')))
        points.update(self._find_all(Element('MALE_ZOMBIE')))
        points.update(self._find_all(Element('ZOMBIE_DIE')))
        return list(points)

    def get_laser_machines(self):
        points = set()
        points.update(self._find_all(Element('LASER_MACHINE_CHARGING_LEFT')))
        points.update(self._find_all(Element('LASER_MACHINE_CHARGING_RIGHT')))
        points.update(self._find_all(Element('LASER_MACHINE_CHARGING_UP')))
        points.update(self._find_all(Element('LASER_MACHINE_CHARGING_DOWN')))
        points.update(self._find_all(Element('LASER_MACHINE_READY_LEFT')))
        points.update(self._find_all(Element('LASER_MACHINE_READY_RIGHT')))
        points.update(self._find_all(Element('LASER_MACHINE_READY_UP')))
        points.update(self._find_all(Element('LASER_MACHINE_READY_DOWN')))
        return list(points)

    def get_lasers(self):
        points = set()
        points.update(self._find_all(Element('LASER_LEFT')))
        points.update(self._find_all(Element('LASER_RIGHT')))
        points.update(self._find_all(Element('LASER_UP')))
        points.update(self._find_all(Element('LASER_DOWN')))
        return list(points)

    def get_boxes(self):
        return self._find_all(Element('BOX'))

    def get_floors(self):
        return self._find_all(Element('FLOOR'))

    def get_holes(self):
        points = set()
        points.update(self._find_all(Element('HOLE')))
        points.update(self._find_all(Element('ROBO_FALLING')))
        points.update(self._find_all(Element('ROBO_OTHER_FALLING')))
        return list(points)

    def get_exits(self):
        return self._find_all(Element('EXIT'))

    def get_starts(self):
        return self._find_all(Element('START'))

    def get_golds(self):
        return self._find_all(Element('GOLD'))

    def get_walls(self):
        points = set()
        points.update(self._find_all(Element('ANGLE_IN_LEFT')))
        points.update(self._find_all(Element('WALL_FRONT')))
        points.update(self._find_all(Element('ANGLE_IN_RIGHT')))
        points.update(self._find_all(Element('WALL_RIGHT')))
        points.update(self._find_all(Element('ANGLE_BACK_RIGHT')))
        points.update(self._find_all(Element('WALL_BACK')))
        points.update(self._find_all(Element('ANGLE_BACK_LEFT')))
        points.update(self._find_all(Element('WALL_LEFT')))
        points.update(self._find_all(Element('WALL_BACK_ANGLE_LEFT')))
        points.update(self._find_all(Element('WALL_BACK_ANGLE_RIGHT')))
        points.update(self._find_all(Element('ANGLE_OUT_RIGHT')))
        points.update(self._find_all(Element('ANGLE_OUT_LEFT')))
        points.update(self._find_all(Element('SPACE')))
        return list(points)

    def get_perks(self):
        points = set()
        points.update(self._find_all(Element('UNSTOPPABLE_LASER_PERK')))
        points.update(self._find_all(Element('DEATH_RAY_PERK')))
        points.update(self._find_all(Element('UNLIMITED_FIRE_PERK')))
        return list(points)
