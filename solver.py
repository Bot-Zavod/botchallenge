#!/usr/bin/env python3
from typing import List, Set
import time

from state_machine import BotStateMachine
from board import Board
from command import Command
from element import Element

from gamepad import GamepadRoboController

""" This class should contain the movement generation algorithm."""
class DirectionSolver:

    def __init__(self):  # initializes on websocket start
        #Place configuration paramters here
        self.FSM = BotStateMachine()

    def get(self, board_string):
        start = time.time()
        current_board = Board(board_string)
        print(current_board.to_string())
        next_cmd = self.FSM.yield_decision(current_board)
        end = time.time()
        print(f"Sending Command: {next_cmd}")
        print(f"The previous decision took {round(end - start, 3)}s")
        return next_cmd

if __name__ == '__main__':
    raise RuntimeError("This module is not intended to be ran from CLI")
