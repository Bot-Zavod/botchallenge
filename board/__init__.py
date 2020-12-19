#! /usr/bin/env python3

from typing import Tuple, List, Set

import json
from math import sqrt
import copy

from element import Element

import board._pathfinding
import board._get_elements
import board._custom


class Board(_get_elements.Mixin, _pathfinding.Mixin, _custom.Mixin):
    COUNT_LAYERS = 3

    def __init__(self):
        self.previous_board: Board = None  # previous board object
        self._board: List[List[str]] = None  # board matrix
        self._board_hash: int = None  # first string hash

    def update_board(
        self, board_string: str, shift_direction: Tuple[int, int] = None
    ) -> bool:
        """ build board and prepare all data """

        # makes previous board independent for changes
        if self._board:
            # drop previous copy to avoid object linked list
            self.previous_board = None
            self.previous_board = copy.deepcopy(self)

        # extracting info from server massage
        board_json = json.loads(board_string)
        self.final_level = (board_json["levelProgress"]["total"]
                            == board_json["levelProgress"]["current"])
        hash_str = board_json["layers"][0][:60]
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
        self._board_hash = hash_str.translate(translation)

        self.levelFinished = board_json["levelFinished"]
        self._layer_size = int(sqrt(len(board_json["layers"][0])))
        self._board = [list(layer) for layer in board_json["layers"]]

        # reusable info
        self._hero = self.get_hero()
        self.directions = ((-1, 0), (1, 0), (0, -1), (0, 1), (0, 0))
        self._jump_over = self.jump_over()
        self._non_barrier = self.non_barrier()
        self._targets = self.get_falling_players() + self.passive_attack_check()

        # if board shifted save bool and shift modifier
        self.board_shifted = False
        if self.previous_board:

            if self.previous_board._board_hash != self._board_hash:
                self.board_shifted = True
                # opposite direction of last player move
                self.shift_direction = shift_direction

                self.starts = self.get_starts()

                self.exits = self.get_exits()
                self.nearest_exit = self.bfs_nearest(self._hero, self.exits)

                self.edge_transitions = self.get_edge_transitions()
                self.nearest_transition = self.bfs_nearest(
                    self._hero, self.edge_transitions)
            else:
                # if board doesn't shift exist and transitions stay the same
                self.starts = self.previous_board.starts

                self.exits = self.previous_board.exits
                self.nearest_exit = self.previous_board.nearest_exit

                self.edge_transitions = self.previous_board.edge_transitions
                self.nearest_transition = self.previous_board.nearest_transition
        else:
            self.starts = self.get_starts()

            self.exits = self.get_exits()
            self.nearest_exit = self.bfs_nearest(self._hero, self.exits)

            self.edge_transitions = self.get_edge_transitions()
            self.nearest_transition = self.bfs_nearest(
                self._hero, self.edge_transitions)

        # MAKING SNAPSHOTS FOR COMPASS
        portals = self.starts + self.exits
        self.snapshots = dict()
        for portal in portals:
            snap = self.make_snapshot(portal)
            if snap:
                self.snapshots[snap] = portal

        self.golds = self.get_golds()
        self.nearest_gold = self.bfs_nearest(self._hero, self.golds)

        self.players = self.get_other_live_heroes()
        self.nearest_player = self.bfs_nearest(self._hero, self.players)

        self.dead_players = self.get_other_dead_heroes()
        self.nearest_dead_player = self.bfs_nearest(
            self._hero, self.dead_players)

        print("nearest_gold: ", self.nearest_gold)
        print("nearest_exit: ", self.nearest_exit)

        return self.board_shifted

    def _find_all(self, elements: List[Element]) -> List[Tuple[int, int]]:
        _points = []

        # group element by layers
        element_layers = {}
        for element in elements:
            _a_char = element.get_char()
            _layer = element.get_layer()
            if _layer in element_layers:
                element_layers[_layer].add(_a_char)
            else:
                element_layers[_layer] = set(_a_char)

        # search elemnt group in cpecific layer
        for layer in element_layers:
            search_elements = element_layers[layer]
            for i in range(len(self._board[layer])):
                # TODO use filter to SPEED UP!!! 🏃👮
                if self._board[layer][i] in search_elements:
                    _points.append(self._strpos2pt(i))
        return _points

    def _strpos2pt(self, strpos):
        return tuple(self._strpos2xy(strpos))

    def _strpos2xy(self, strpos):
        return strpos % self._layer_size, strpos // self._layer_size

    def _xy2strpos(self, x, y):
        return self._layer_size * y + x

    def to_string(self):
        return (
            "Board:\n{brd}\nHero at: {hero}\n"
            "Golds at: {gld}\nPerks at: {prk}".format(
                brd=self._line_by_line(),
                hero=self.get_hero(),
                gld=self.get_golds(),
                prk=self.get_perks(),
            )
        )

    def _line_by_line(self):
        _string_board = "  "
        for i in range(self._layer_size * Board.COUNT_LAYERS):
            _string_board += str(i % 10)
            if (i + 1) % self._layer_size == 0:
                _string_board += "\t"

        _string_board += "\n"

        for i in range(self._layer_size):
            _string_board += str(i % 10) + " "
            for j in range(Board.COUNT_LAYERS):
                for k in range(self._layer_size):
                    _string_board += self._board[j][k + (i * self._layer_size)]
                _string_board += "\t"
            _string_board += "\n"

        return _string_board


if __name__ == "__main__":
    raise RuntimeError("This module is not designed to be ran from CLI")
