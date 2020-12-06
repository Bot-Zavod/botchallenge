from typing import Tuple, List, Set
from element import Element

from board._element_groups import _ELEMENT_GROUPS


class Mixin:

    # def is_near(self, x, y, elem):
    #     _is_near = (self.is_at(x + 1, y, elem) or
    #                 self.is_at(x - 1, y, elem) or
    #                 self.is_at(x, 1 + y, elem) or
    #                 self.is_at(x, 1 - y, elem))
    #     return _is_near

    # def count_near(self, x, y, elem):
    #     _near_count = 0
    #     if not Point(x, y).is_bad(self._layer_size):
    #         for _x, _y in ((x + 1, y), (x - 1, y), (x, 1 + y), (x, 1 - y)):
    #             if self.is_at(_x, _y, elem):
    #                 _near_count += 1
    #     return _near_count

    def get_actionspace(self) -> Set[Tuple[int, int]]:
        """ Returns possible and save actions """

        # TODO should work with action beacause stat on place and jump
        # have the same coordinate but dufferent timing
        # + we can jump to wall, to stay in air and finish no neighbour cell

        directions = self.directions
        hero = self._hero
        hero_step = {
            (hero[0] + act[0], hero[1] + act[1]) for act in directions}
        hero_jump = {
            (hero[0] + act[0] * 2, hero[1] + act[1] * 2) for act in directions}

        # lasers position on first step
        first_lasers = set(
            laser for lasers in self.first_lasers for laser in lasers
        )
        # lasers position on second step
        second_lasers = self.check_second_lasers()

        hero_step = hero_step - first_lasers
        hero_jump = hero_jump - second_lasers

        laser_actionspace = hero_step.union(hero_jump)
        return laser_actionspace

    def is_barrier_at(self, x, y):
        return (x, y) not in self._non_barrier

    def non_barrier(self):
        # returns set of non barrier coordinates
        elements = _ELEMENT_GROUPS["WALKABLE"]
        points = self._find_all([Element(el) for el in elements])
        return points

    def second_layer_barrier(self):
        """ objects on second layer that stop lasers """

        elements = _ELEMENT_GROUPS["LASER_MACHINES"] + ["BOX"]
        points = self._find_all([Element(el) for el in elements])
        return points

    def jump_over(self):
        """ object hero can jump over """

        elements = _ELEMENT_GROUPS["LASER_MACHINES"] + ["BOX", "HOLE"]
        points = self._find_all([Element(el) for el in elements])
        return points

    def check_first_lasers(self) -> List[Set[Tuple[int, int]]]:
        # step is predicting lasers on specific sec
        points = [list()] * 4  # left, right, up, down

        possible_lasers = ("LASER_LEFT", "LASER_RIGHT",
                           "LASER_UP", "LASER_DOWN")
        charged_guns = (
            "LASER_MACHINE_READY_LEFT",
            "LASER_MACHINE_READY_RIGHT",
            "LASER_MACHINE_READY_UP",
            "LASER_MACHINE_READY_DOWN",
        )
        directions = self.directions[:-1]
        # Calculate all points for next Lasers
        for i, laser_dir, machine, action in zip(
            range(3), possible_lasers, charged_guns, directions
        ):
            lasers = self._find_all([Element(laser_dir), Element(machine)])
            points[i] = [(laser[0] + action[0],
                          laser[1] + action[1]) for laser in lasers]
        return points

    def check_second_lasers(self) -> Set[Tuple[int, int]]:
        first_lasers = self.first_lasers
        second_layer_barrier = self.second_layer_barrier()
        directions = self.directions[:-1]
        second_lasers = set()

        for i, lasers in enumerate(first_lasers):
            for laser in lasers:
                if laser not in second_layer_barrier:
                    second_lasers.add(
                        (laser[0] + directions[i][0],
                         laser[1] + directions[i][1])
                    )
        return second_lasers

    def check_danger_enemies(self):
        hero_coords = self.get_hero()
        # Check if zombies are anywhere near

        elements = _ELEMENT_GROUPS["ZOMBIE"]
        points = self._find_all([Element(el) for el in elements])

        directions = self.directions
        zombie_moves = set()
        for zombie in zombies:
            for action in directions:
                zombie_moves.add((zombie[0] + action[0],
                                  zombie[1] + action[1]))

        player_moves = set()
        for action in directions[:-1]:
            player_moves.add((hero_coords[0] + action[0],
                              hero_coords[1] + action[1]))
            player_moves.add((hero_coords[0] + action[0] * 2,
                              hero_coords[1] + action[1] * 2))

        points = player_moves & zombie_moves

        return points

    def is_me_alive(self) -> bool:
        elements = _ELEMENT_GROUPS["ROBO_DEAD"]
        points = self._find_all([Element(el) for el in elements])
        return len(points) == 0
