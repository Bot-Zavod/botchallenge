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

        # TODO should work with action beacause stay on place and jump
        # have the same coordinate but dufferent timing
        # + we can jump to wall, to stay in air and finish on neighbour cell

        directions = self.directions
        hero = self._hero

        non_barrier = set(self.non_barrier())

        first_lasers, second_lasers = self.check_lasers()
        first_zombies, second_zombies = self.check_zombies()
        players_shots = self.check_players_shoots()
        players = set(self._find_all([Element("ROBO_OTHER")]))

        hero_step = {
            (hero[0] + act[0],
             hero[1] + act[1]) for act in directions
        }
        hero_jump = {
            (hero[0] + act[0] * 2,
             hero[1] + act[1] * 2) for act in directions
        }

        # we can step here
        hero_step = ((hero_step & non_barrier)
                     - first_lasers - first_zombies - players_shots - players)

        # TODO check wall jumps
        hero_jump = (hero_jump & non_barrier) - second_lasers - second_zombies

        actionspace = hero_step.union(hero_jump)
        print("actionspace: ", actionspace)
        return actionspace

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

    def check_lasers(self) -> Tuple[Set[Tuple[int, int]]]:
        """ predicting lasers on first and second sec """

        first_points = set()
        second_points = set()

        hero = self._hero
        directions = self.directions[:-1]
        second_layer_barrier = self.second_layer_barrier()

        lasers = ("LASER_LEFT", "LASER_RIGHT",
                  "LASER_UP", "LASER_DOWN")
        charged_guns = (
            "LASER_MACHINE_READY_LEFT",
            "LASER_MACHINE_READY_RIGHT",
            "LASER_MACHINE_READY_UP",
            "LASER_MACHINE_READY_DOWN",
        )
        # Calculate all points for next Lasers
        for laser_dir, machine, action in zip(
                lasers, charged_guns, directions
            ):
            possible_lasers = self._find_all([Element(laser_dir),
                                              Element(machine)])
            for laser in possible_lasers:
                laser_first_move = (laser[0] + action[0],
                                    laser[1] + action[1])
                if laser_first_move not in second_layer_barrier:
                    first_points.add(laser_first_move)
                    # we couldn't step to the laser direction
                    if laser_first_move == hero:
                        first_points.add(laser)
                    laser_second_move = (laser[0] + action[0] * 2,
                                         laser[1] + action[1] * 2)
                    second_points.add(laser_second_move)
        return first_points, second_points

    def check_zombies(self) -> Tuple[Set[Tuple[int, int]]]:
        """ predicting zombies on first and second sec """

        first_points = set()
        second_points = set()

        hero = self._hero
        directions = self.directions[:-1]
        previous_board = self.previous_board

        elements = _ELEMENT_GROUPS["ZOMBIE"]
        current_zombies = self._find_all([Element(el) for el in elements])
        if previous_board:
            previous_zombies = previous_board._find_all(
                [Element(el) for el in elements])
        else:
            previous_zombies = []

        if self.board_shifted:
            # if shifted adapt to new coordinates
            shift = self.shift_direction
            for i in range(len(previous_zombies)):
                zombie = previous_zombies[i]
                previous_zombies[i] = (zombie[0] + shift[0],
                                       zombie[1] + shift[1])

        # zombies moves every two secs
        for zombie in current_zombies:
            if zombie in previous_zombies:  # will step
                for action in directions:
                    zombie_step = (zombie[0] + action[0], zombie[1] + action[1])
                    if zombie_step == hero:
                        first_points.add(zombie)
                    first_points.add(zombie_step)
                    second_points.add(zombie_step)
            else:  # will wait in its place
                first_points.add(zombie)
                for action in directions:
                    zombie_step = (zombie[0] + action[0], zombie[1] + action[1])
                    second_points.add(zombie_step)

        return first_points, second_points

    def check_players_shoots(self) -> Set[Tuple[int, int]]:
        """ all possible directions on whicj players can fire """

        players = self._find_all([Element("ROBO_OTHER")])
        directions = self.directions[:-1]

        players_shots = set()
        for player in players:
            for d in directions:
                players_shots.add((player[0] + d[0],
                                   player[1] + d[1]))
        return players_shots

    def is_me_alive(self) -> bool:
        elements = _ELEMENT_GROUPS["ROBO_DEAD"]
        points = self._find_all([Element(el) for el in elements])
        return len(points) == 0

    def is_me_jumping(self) -> bool:
        points = self._find_all([Element("ROBO_FLYING")])
        return len(points) == 1

    def passive_attack_check(self) -> List[Tuple[int, int]]:
        """ check targets to kill in our vision """

        directions = self.directions[:-1]  # cut stay state
        hero = self._hero
        elements = _ELEMENT_GROUPS["TARGETS"]
        targets = self._find_all([Element(el) for el in elements])

        fire_range = 3
        reachable_targets = []

        for r in range(fire_range):
            for d in directions:
                trg = (hero[0] + d[0]*r, hero[1] + d[1]*r)
                if trg in targets:
                    reachable_targets.append(trg)
        return reachable_targets

    def get_edge_transitions(self) -> List[Tuple[int, int]]:
        edges = set(
            [(x, 0) for x in range(0, 20)] +
            [(x, 19) for x in range(0, 20)] +
            [(0, y) for y in range(1, 19)] +
            [(19, y) for y in range(1, 19)]
        )
        floor = Element("FLOOR").get_char()
        transitions = []
        for edge in edges:
            _strpos = self._xy2strpos(*edge)
            if self._board[0][_strpos] == floor:
                transitions.append(edge)
        return transitions
