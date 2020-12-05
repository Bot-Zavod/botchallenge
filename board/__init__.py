#! /usr/bin/env python3

from math import sqrt
from element import Element
import re

from typing import Tuple, List, Set

import board._pathfinding
import board._get_elements
import board._custom


class Board(_get_elements.Mixin, _pathfinding.Mixin, _custom.Mixin):
    COUNT_LAYERS = 3
    INPUT_REGEX = "(.*),\"layers\":\[(.*)\](.*)"

    def __init__(self, input):
        matcher = re.search(Board.INPUT_REGEX, input)
        board_string = matcher.group(2).replace('\n', '').replace(',', '').replace('\"', '')  # one line board

        self._board = []
        _layer_len = int(len(board_string) / Board.COUNT_LAYERS)
        for i in range(Board.COUNT_LAYERS):
            _layer = []
            for j in range(_layer_len):
                _layer.append(board_string[j + (i * _layer_len)])
            self._board.append(_layer)
        self._layer_size = int(sqrt(_layer_len))

        self._jump_over = self.jump_over()
        self._non_barrier = self.non_barrier()
        self._hero = self.get_hero()

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

    def is_at(self, x, y, element_object):
        return element_object in self.get_at(x, y)

    # def is_near(self, x, y, elem):
    #     _is_near = False
    #     if not Point(x, y).is_bad(self._layer_size):
    #         _is_near = (self.is_at(x + 1, y, elem) or
    #                     self.is_at(x - 1, y, elem) or
    #                     self.is_at(x, 1 + y, elem) or
    #                     self.is_at(x, 1 - y, elem))
    #     return _is_near

    # def count_near(self, x, y, elem):
    #     _near_count = 0
    #     if not Point(x, y).is_bad(self._layer_size):
    #         for _x, _y in ((x + 1, y), (x - 1, y), (x, 1 + y), (x, 1 - y)):
    #             if self.is_at(_x, _y, elem):
    #                 _near_count += 1
    #     return _near_count

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
  
    
def mht_dist(start: Tuple[int, int], end: Tuple[int, int]):
    return ((end[0] - start[0]) ** 2) + ((end[1] - start[1]) ** 2)


if __name__ == '__main__':
    raise RuntimeError("This module is not designed to be ran from CLI")
