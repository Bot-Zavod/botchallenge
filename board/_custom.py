from typing import Tuple, List, Set
from element import Element

from board._element_groups import _ELEMENT_GROUPS


class Mixin:

    edges = set(
        [(x, 0) for x in range(0, 20)] +
        [(x, 19) for x in range(0, 20)] +
        [(0, y) for y in range(1, 19)] +
        [(19, y) for y in range(1, 19)]
    )

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

    def get_actionspace(self) -> Set[Tuple[int, int, int]]:
        """ Returns possible and save actions """

        directions = self.directions
        hero = self._hero

        non_barrier = set(self.non_barrier())
        second_layer_barrier = set(self.second_layer_barrier())

        first_lasers, second_lasers = self.check_lasers()
        first_overlayed_lasers, second_overlayed_lasers = self.get_overlayed_lasers()
        first_zombies, second_zombies = self.check_zombies()
        players_shots = self.check_players_shoots()

        hero_step, hero_jump = set(), set()
        for act in directions:  # all hero moves based on barriers
            step = (hero[0] + act[0], hero[1] + act[1])
            if step in non_barrier:
                hero_step.add(step)

            jump = (hero[0] + act[0] * 2, hero[1] + act[1] * 2)
            if jump in second_layer_barrier:  # jump on wall
                if step in non_barrier:
                    jump = step
                else:
                    continue
            elif jump not in non_barrier:
                continue
            hero_jump.add(jump)

        hero_step = (
            hero_step - first_lasers -
            first_zombies - players_shots -
            first_overlayed_lasers
        )
        hero_jump = (
            hero_jump - second_lasers -
            second_zombies - second_overlayed_lasers
        )

        hero_step_actions = [(*step, -1) for step in hero_step]
        hero_jump_actions = [(*jump, 1) for jump in hero_jump]

        actionspace = set(hero_step_actions + hero_jump_actions)
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
                lasers, charged_guns, directions):
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
                    zombie_step = (zombie[0] + action[0],
                                   zombie[1] + action[1])
                    if zombie_step == hero:
                        first_points.add(zombie)
                    first_points.add(zombie_step)
                    second_points.add(zombie_step)
            else:  # will wait in its place
                first_points.add(zombie)
                for action in directions:
                    zombie_step = (zombie[0] + action[0],
                                   zombie[1] + action[1])
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

    def get_hero_move(self) -> Tuple[int, int]:
        if self.previous_board:
            previous_hero = self.previous_board._hero
            hero = self._hero
            if self.board_shifted:
                shift = self.shift_direction
                previous_hero = (previous_hero[0] + shift[0],
                                 previous_hero[1] + shift[1])
            hero_move = (hero[0] - previous_hero[0], hero[1] - previous_hero[1])
            return hero_move
        else:
            return (0, 0)

    def make_snapshot(self, center: Tuple[int, int]) -> str:
        """ create string snapshot of first start position """

        hero = self._hero

        for i in (0, 1):  # check that we sea full surraunding
            if not(2 <= center[i] <= 17):
                if not(4 > hero[i] or hero[i] > 15):
                    return ""

        translation = {  # dynamic elements of static board
            "◄": "˂",
            "►": "˃",
            "▲": "˄",
            "▼": "˅",
            "$": ".",
            "l": ".",
            "r": ".",
            "f": ".",
        }
        translation = {ord(key): ord(value) for key, value in translation.items()}
        _strpos = self._xy2strpos(*center)
        snapshot = self._board[0][_strpos]  # S or E
        for y in range(-2, 3):
            for x in range(-2, 3):
                x_pos = center[0] + x
                y_pos = center[1] + y
                if not(0 <= x_pos <= 19 and 0 <= y_pos <= 19):  # cut adges
                    continue

                _strpos = self._xy2strpos(x, y)
                snapshot += self._board[0][_strpos]
        return snapshot.translate(translation)

    def is_me_alive(self) -> bool:
        elements = _ELEMENT_GROUPS["ROBO_DEAD"]
        points = self._find_all([Element(el) for el in elements])
        return len(points) == 0

    def is_me_jumping(self) -> bool:
        points = self._find_all([Element("ROBO_FLYING")])
        return len(points) == 1

    def collected_gold(self) -> bool:
        hero = self._hero
        previous_board = self.previous_board

        if self.board_shifted:  # if shifted adapt to new coordinates
            shift = self.shift_direction
            cell_before = (hero[0] + shift[0], hero[1] + shift[1])
        else:
            cell_before = hero

        _strpos = self._xy2strpos(*cell_before)
        if previous_board and previous_board._board[0][_strpos] == "$":
            return True
        return False

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
        return list(reachable_targets)

    def get_edge_transitions(self) -> List[Tuple[int, int]]:
        """ map edge transitions to another parts of map """

        edges = Mixin.edges
        floor = Element("FLOOR").get_char()
        transitions = []
        for edge in edges:
            _strpos = self._xy2strpos(*edge)
            if self._board[0][_strpos] == floor:
                transitions.append(edge)
        return transitions

    def get_overlayed_lasers(self) -> List[Tuple[int, int]]:
        """
            if we in one cell shoot to other player
            he may shoot in us too
            lasers ovwrlay and we don't sea it
            so couldn't go toward him or stay in place
        """

        directions = self.directions[:-1]
        hero = self._hero
        players = self._find_all([Element("ROBO_OTHER")])
        lasers = self.get_lasers()

        first_points, second_points = set(), set()
        for act in directions:
            possible_enemy = (hero[0] + act[0] * 2, hero[1] + act[1] * 2)
            if possible_enemy in players:  # jump on wall
                overlaid_laser = (hero[0] + act[0], hero[1] + act[1])
                if overlaid_laser in lasers:
                    first_points.add(overlaid_laser)

        # if we have overlaid lasers they will go to us on 2 sec
        if first_points:
            second_points.add(hero)

        return first_points, second_points

    def get_falling_players(self) -> List[Tuple[int, int]]:
        """ place near hero were will fall other hero """

        hero = self._hero
        directions = self.directions
        previous_board = self.previous_board
        if not previous_board:
            return []
        flying_players = self._find_all([Element("ROBO_OTHER_FLYING")])
        previous_players = previous_board._find_all([Element("ROBO_OTHER")])

        if self.board_shifted:
            # if shifted adapt to new coordinates
            shift = self.shift_direction
            for i in range(len(previous_players)):
                player = previous_players[i]
                previous_players[i] = (player[0] + shift[0],
                                       player[1] + shift[1])

        landing_points = set()
        for y in range(-2, 3):
            for x in range(-2, 3):
                air_cell = (hero[0] + x, hero[1] + y)
                if air_cell in flying_players:
                    for act in directions:
                        previous_player = (air_cell[0] + act[0],
                                           air_cell[1] + act[1])
                        if previous_player in previous_players:
                            landing = (air_cell[0] + (air_cell[0] - previous_player[0]),
                                       air_cell[0] + (air_cell[0] - previous_player[0]))
                            landing_points.add(landing)

        hero_shoot = set()
        for act in directions[:-1]:
            hero_shoot.add((hero[0] + act[0],
                            hero[1] + act[1]))
        death_point = hero_shoot & landing_points
        return list(death_point)
