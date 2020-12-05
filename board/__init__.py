#! /usr/bin/env python3

from math import sqrt
from element import Element
import json
import re

from typing import Tuple, List, Set

import board._pathfinding
import board._get_elements
import board._custom


class Board(_get_elements.Mixin, _pathfinding.Mixin, _custom.Mixin):
    COUNT_LAYERS = 3

    def __init__(self, input):
        board_json = json.loads(input)
        self._layer_size = int(sqrt(len(board_json["layers"][0])))
        self._board = [list(layer) for layer in board_json["layers"]]
        self.levelFinished = board_json["levelFinished"]
        # self._hero = (board_json["heroPosition"]["x"], board_json["heroPosition"]["y"]) # gives error coordinates
        
        
        # reusable info
        self._hero = self.get_hero()
        self.directions = ((-1,0), (1,0), (0,-1), (0,1), (0,0))
        self._jump_over = self.jump_over()
        self._non_barrier = self.non_barrier()
        self.golds = set(self.get_golds())
        self.exits = set(self.get_exits())
        self.nearest_gold = self.bfs_nearest(self._hero, self.golds)
        self.nearest_exit = self.bfs_nearest(self._hero, self.exits)
        
        self.first_lasers = self.check_first_lasers()

    def _find_all(self, element: Element) -> List[Tuple[int, int]]:
        _points = []
        _a_char = element.get_char()
        for i in range(len(self._board)):
            for j in range(len(self._board[i])):
                if self._board[i][j] == _a_char:
                    _points.append(self._strpos2pt(j))
        return _points

    def _strpos2pt(self, strpos):
        return tuple(self._strpos2xy(strpos))

    def _strpos2xy(self, strpos):
        return strpos % self._layer_size, strpos // self._layer_size

    def _xy2strpos(self, x, y):
        return self._layer_size * y + x

    def to_string(self):
        return ("Board:\n{brd}\nHero at: {hero}\nOther Heroes "
                "at: {others}\nZombies at: {zmb}\nLasers at:"
                " {lsr}\nHoles at : {hls}\nGolds at: "
                "{gld}\nPerks at: {prk}".format(brd=self._line_by_line(),
                                                  hero=self.get_hero(),
                                                  others=self.get_other_heroes(),
                                                  zmb=self.get_zombies(),
                                                  lsr=self.get_lasers(),
                                                  hls=self.get_holes(),
                                                  gld=self.get_golds(),
                                                  prk=self.get_perks())
                )

    def _line_by_line(self):
        _string_board = '  '
        for i in range(self._layer_size * Board.COUNT_LAYERS):
            _string_board += str(i % 10)
            if (i + 1) % self._layer_size == 0:
                _string_board += '\t'

        _string_board += '\n'

        for i in range(self._layer_size):
            _string_board += str(i % 10) + ' '
            for j in range(Board.COUNT_LAYERS):
                for k in range(self._layer_size):
                    _string_board += self._board[j][k + (i * self._layer_size)]
                _string_board += '\t'
            _string_board += '\n'

        return _string_board


if __name__ == '__main__':
    raise RuntimeError("This module is not designed to be ran from CLI")
