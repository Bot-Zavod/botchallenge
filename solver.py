#!/usr/bin/env python3

import time

from state_machine import BotStateMachine
from gamepad import GamepadRoboController


class DirectionSolver:
    """ This class should contain the movement generation algorithm."""

    def __init__(self):  # initializes on websocket start
        # Place configuration paramters here
        self.FSM = BotStateMachine()

    def get(self, board_string: str) -> str:
        start = time.time()
        next_cmd = self.FSM.yield_decision(board_string)
        end = time.time()
        print(f"The previous decision took {round(end - start, 3)}s\n\n")
        return next_cmd


if __name__ == '__main__':
    raise RuntimeError("This module is not intended to be ran from CLI")
