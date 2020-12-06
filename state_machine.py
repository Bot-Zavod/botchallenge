from typing import Tuple, List
from functools import wraps

import requests

from board import Board


def state_control(func):
    """ check if function corresponds to the state """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        func_name = func.__name__
        state_code = self.state_methods_names.index(func_name)
        actual_state_code = self.stateStack[-1].code
        if actual_state_code != state_code:
            for name, code in self.states.items():
                if code == actual_state_code:
                    state_name = name
            error_text = f"Trying to run <{func_name}> in <{state_name}> state"
            raise Exception(error_text)
        return func(self, *args, **kwargs)

    return wrapper


class State:
    """ defines our action based on our goal """

    # TODO func to recalculate stateGoal and plannedPath based on board shift

    def __init__(self, code: int, goal: Tuple[int, int] = None):
        self.code = code  # BotStateMachine.states index
        # Priority states cannot be switched
        self.priority = False
        # State may or may not have a goal and planned path
        # e.g Walk to exit has one, dodge doesnt
        self.stateGoal: Tuple[int, int] = goal
        self.plannedPath: List[tuple[int, int]] = None

    def pop_path_node(self, hero: Tuple[int, int] = None) -> Tuple[int, int]:
        """ return next step of our path in case we are not standing there """

        if not self.plannedPath:
            raise Exception("no plannedPath in pop_path_node")
        next_node = self.plannedPath.pop(0)
        if next_node == hero:
            if not self.plannedPath:
                raise Exception("no fearther plannedPath after next_node")
            next_node = self.plannedPath.pop(0)
        return next_node

    def shift_coord(self, shift: Tuple[int, int]) -> None:
        # tuples could not be edited so we rewrite them
        if self.stateGoal:
            self.stateGoal = (self.stateGoal[0] + shift[0],
                              self.stateGoal[1] + shift[1])
        if self.plannedPath:
            for i in range(len(self.plannedPath)):
                cell = self.plannedPath[i]
                self.plannedPath[i] = (cell[0] + shift[0],
                                       cell[1] + shift[1])

    def check_goal(self, check_coords: Tuple[int, int]) -> bool:
        """ are we already on our target coordinate """
        return check_coords == self.stateGoal

    def reset(self) -> None:
        """ reset target state data """

        self.priority = False
        self.stateGoal = None
        self.plannedPath = None

    def dropPath(self) -> None:
        self.plannedPath = None

    def __str__(self) -> str:
        return f"State #{self.code} Goal: {self.stateGoal}"

    def __repr__(self) -> str:
        return BotStateMachine.state_names[self.code]


class BotStateMachine:
    # control variables
    url = "https://epam-botchallenge.com/codenjoy-balancer/rest/game/settings/get"
    controls = requests.get(url).json()[0]
    # perkAvailability  = controls["perkAvailability"]
    # gunRecharge       = controls["gunRecharge"]
    # deathRayRange     = controls["deathRayRange"]
    # gunShotQueue      = controls["gunShotQueue"]
    # gunRestTime       = controls["gunRestTime"]
    # roomSize          = controls["roomSize"]
    # loosePenalty      = controls["loosePenalty"]
    # killHeroScore     = controls["killHeroScore"]
    # killZombieScore   = controls["killZombieScore"]
    # goldScore         = controls["goldScore"]
    # winScore          = controls["winScore"]
    # trainingMode      = controls["trainingMode"]
    # enableKillScore   = controls["enableKillScore"]
    # perkDropRatio     = controls["perkDropRatio"]
    # perkActivity      = controls["perkActivity"]

    # DEATH - Resets all
    states = {
        "REBIRTH": 0,
        "EXIT": 1,
        "GOLD": 2,
        "ACTIVE_HUNT": 3,
        "PASSIVE_HUNT": 4,
        "DODGE": 5,
    }
    # for __repr__ State
    state_names = {value: key for key, value in states.items()}

    def __init__(self):
        # Initialize state_methods
        self.state_methods = (
            self._rebirth,
            self._exit,
            self._gold,
            self._active_hunt,
            self._passive_hunt,
            self._dodge,
        )
        # required for state_control decorator
        self.state_methods_names = list(func.__name__ for func in self.state_methods)

        # Initialize ❤️ base player state
        self.firingTimer = 0
        self.goldCollected = 0
        self.activeBonus = None
        self.bonusTerm = 0

        # In state-goal stack states are stored with goals
        self.stateStack: List[State] = []

        self.board: Board = Board()

        # culculate shift
        # for jump stays the same move
        self.shift_direction: Tuple[int, int] = None

    def yield_decision(self, board_string: str) -> str:
        # TODO save previous bourd and calculate shift

        # update board
        board_shifted = self.board.update_board(board_string,
                                                self.shift_direction)
        # if new board first layer differs from previous
        # we need to shift our goals and paths
        if board_shifted:
            self.shift_stack()
        print(self.board.to_string(), "\n")

        print("previous_board:\t", self.board.previous_board)
        print("current_board:\t", self.board)

        # Get battlefield information
        self.hero = self.board._hero
        self.exits = self.board.exits
        self.golds = self.board.golds
        self.actionspace = self.board.get_actionspace()

        # rebirth if killed
        if not self.board.is_me_alive():
            self.append_stack("REBIRTH")

        # passive hunt if possible to kill someone
        # if not self.stateStack[-1].priority:
        #     self.append_stack("PASSIVE_HUNT")

        next_move = self.act_state()

        # debug info
        print("state Stack: ", self.stateStack)
        if self.stateStack:
            current_state = self.stateStack[-1]
            print("state Goal: ", current_state.stateGoal)
            print("state plannedPath: ", current_state.plannedPath)

        # saving directin of our move to it to board on update
        next_cmd, self.shift_direction = self._cmd_to_action(next_move)
        print("shift_direction: ", self.shift_direction)
        print(f"Sending Command: {next_cmd}")
        return next_cmd

    def act_state(self) -> Tuple[int, int, int]:
        """ set state if none and return top state action """

        if not self.stateStack:  # If state is None - choose another one
            if self.board.nearest_gold:
                self.append_stack("GOLD")
            elif self.board.nearest_exit:
                self.append_stack("EXIT")

        return self.state_methods[self.stateStack[-1].code]()

    def append_stack(
        self, state_name: str, goal: Tuple[int, int] = None
    ) -> None:
        if state_name in BotStateMachine.states:
            self.stateStack.append(State(BotStateMachine.states[state_name], goal=goal))
        else:
            raise Exception(f"Tring to append non excisting {state_name} to stateStack")

    def shift_stack(self) -> None:
        for state in self.stateStack:
            state.shift_coord(self.shift_direction)

    def _cmd_to_action(
        self, action: Tuple[int, int, int]
    ) -> Tuple[str, Tuple[int, int]]:
        """ transforms coordinates and action code to server command """

        if not action:
            return "", (0, 0)

        cmd_dir = ""
        hero = self.hero

        # Jump on my place
        if action[:2] == hero[:2] and action[2] == 1:
            return "ACT(1)", (0, 0)

        if hero[0] > action[0]:
            cmd_dir = "LEFT"
            shift = (-1, 0)
        elif hero[0] < action[0]:
            cmd_dir = "RIGHT"
            shift = (1, 0)
        elif hero[1] > action[1]:
            cmd_dir = "UP"
            shift = (0, -1)
        elif hero[1] < action[1]:
            cmd_dir = "DOWN"
            shift = (0, 1)

        cmd_code = action[2]
        cmd_prefix = ""
        if cmd_code in (1, 2, 3):
            cmd_prefix += f"ACT({cmd_code}),"

        if cmd_code == 3:
            shift = (0, 0)

        return cmd_prefix + cmd_dir, shift

    def _check_jump(self, dest: Tuple[int, int]) -> bool:
        """ check if passed coordinates need jump to reach it """

        return abs((dest[0] - self.hero[0]) + (dest[1] - self.hero[1])) > 1

    def _next_move_calculation(self, state: State) -> Tuple[int, int, int]:
        """ check plannedPath and get next move """

        if not state.plannedPath:
            state.plannedPath = self.board.astar(self.hero, state.stateGoal)

        next_node = state.pop_path_node(hero=self.hero)

        if next_node:
            if self._check_jump(next_node):
                code = 1  # jump code
            else:
                code = -1  # ignore code for walk
            next_move = (*next_node, code)
        else:
            raise Exception("no next_node to use")

        # Make sure it`s safe
        if next_node in self.actionspace:
            return next_move  # If it`s safe - act as planned
        else:
            # If it`s unsafe - dodge
            self.append_stack("DODGE", goal=state.stateGoal)
            return self.act_state()

    """
    STATES FUNCTIONS
    """

    @state_control
    def _rebirth(self) -> tuple:
        """ if we are dead, reset else standing on exit, try to shoot """

        # TODO check if we can kill anyone
        # Reset all stuff
        self.__init__()
        return ()

    @state_control
    def _exit(self) -> Tuple[int, int, int]:
        """ searching for exit """

        state = self.stateStack[-1]

        hero = self.hero
        exits = self.exits

        if not exits:
            # Leave the state, if there`s no exits
            self.stateStack.pop()
            return self.act_state()
        else:
            if state.check_goal(hero):  # If the exit is reached, rebirth
                self.append_stack("REBIRTH")
                return self.act_state()

            if not state.stateGoal:  # check if we have goal
                state.stateGoal = self.board.bfs_nearest(
                    hero, exits
                )  # find nearest exit
                if not state.stateGoal:  # no exit avaliable
                    self.stateStack.pop()
                    return self.act_state()

            return self._next_move_calculation(state)

    @state_control
    def _gold(self) -> Tuple[int, int, int]:
        """ searching for gold """

        state = self.stateStack[-1]

        hero = self.hero

        if not self.board.nearest_gold:
            self.stateStack.pop()
            return self.act_state()
        else:
            # TODO check if gold exists

            # This is called when we pick the gold we looked for,
            # but there`s gold on the map elsewhre
            if state.check_goal(hero):
                self.goldCollected += 1
                state.reset()

            state.stateGoal = self.board.nearest_gold

            return self._next_move_calculation(state)

    @state_control
    def _dodge(self):
        """ find action nearest to target by manhetan distance """

        state = self.stateStack[-1]
        target = state.stateGoal
        state.dropPath()

        lowest_dist = float("inf")
        optimal_move = None
        for action in self.actionspace:
            dist = self.board._mht_dist(action, target)
            if dist < lowest_dist:
                lowest_dist = dist
                optimal_move = action

        if self._check_jump(optimal_move):
            code = 1  # jump code
        else:
            code = -1  # ignore code for walk
        self.stateStack.pop()
        return (*optimal_move, code)

    @state_control
    def _passive_hunt(self):
        # TODO check sanity of attack
        pass

    @state_control
    def _active_hunt(self):
        # TODO kill anyone on this field
        pass
