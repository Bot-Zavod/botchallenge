from typing import Tuple, List
from functools import wraps

import requests

from board import Board
from exit_compass import ExitCompass


def state_control(func):
    """ check if function corresponds to the state """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        func_name = func.__name__
        state_code = self.state_methods_names.index(func_name)
        actual_state_code = self.stateStack[-1].code
        if actual_state_code != state_code:
            state_name = ""
            for name, code in self.states.items():
                if code == actual_state_code:
                    state_name = name
            error_text = f"Trying to run <{func_name}> in <{state_name}> state"
            raise Exception(error_text)
        return func(self, *args, **kwargs)

    return wrapper


exit_compass = ExitCompass()


class State:
    """ defines our action based on our goal """

    def __init__(self, code: int, goal: Tuple[int, int] = None):
        # maybe pass LAMDA in conditions
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

    def shift_coord(self, shift: Tuple[int, int]) -> bool:
        # tuples could not be edited so we rewrite them

        if self.stateGoal:
            self.stateGoal = (self.stateGoal[0] + shift[0],
                              self.stateGoal[1] + shift[1])
            if self.code == BotStateMachine.states["EXPLORE"]:
                #  explore state is not safe on shift
                return True

        if self.plannedPath:
            for i in range(len(self.plannedPath)):
                cell = self.plannedPath[i]
                self.plannedPath[i] = (cell[0] + shift[0],
                                       cell[1] + shift[1])
        return False

    def check_goal(self, hero: Tuple[int, int]) -> bool:
        """ if are we already on our target coordinate """
        return hero == self.stateGoal

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
    gunRecharge = controls["gunRecharge"]
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
        "JUMP": 6,
        "LOOT": 7,
        "EXPLORE": 8,
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
            self._jump,
            self._loot,
            self._explore,
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
        self.hero_rel_pos: Tuple[int, int] = (0, 0)
        self.hero_start_image: str = None

    def yield_decision(self, board_string: str) -> str:
        # update board
        self.set_up_board(board_string)

        if self.firingTimer > 0:  # recharginf the gun
            self.firingTimer -= 1

        # rebirth if killed
        if not self.board.is_me_alive():
            self.append_stack("REBIRTH")

        # do nothing if jumping
        if self.board.is_me_jumping():
            self.append_stack("JUMP")

        # passive hunt if possible to kill someone
        if self.board._targets:
            print(self.board._targets)
            self.append_stack("PASSIVE_HUNT")

        next_move = self.act_state()

        # debug info
        print("state Stack: ", self.stateStack)
        if self.stateStack:
            current_state = self.stateStack[-1]
            print("state Goal: ", current_state.stateGoal)

        # saving directin of our move to it to board on update
        next_cmd, self.shift_direction = self._cmd_to_action(next_move)
        print("shift_direction: ", self.shift_direction)
        print(f"Sending Command: {next_cmd}")
        return next_cmd

    def set_up_board(self, board_string: str):
        board_shifted = self.board.update_board(board_string,
                                                self.shift_direction)
        # if new board first layer differs from previous
        # we need to shift our goals and paths
        if board_shifted:
            self.shift_stack()
        print(self.board.to_string(), "\n")

        if not self.board.previous_board:
            exit_compass.clean_compass()

        self.hero = self.board._hero

        # update relative position from start
        hero_move = self.board.get_hero_move()
        self.hero_rel_pos = (self.hero_rel_pos[0] + hero_move[0],
                             self.hero_rel_pos[1] + hero_move[1])
        if not self.board.previous_board:  # hero spawned on start
            self.hero_start_image = self.board.make_snapshot(self.hero)
        print("hero_rel_pos: ", self.hero_rel_pos)
        print("gold Collected: ", self.goldCollected)

        for dest, coords in self.board.snapshots.items():
            hero_portal_vec = exit_compass._comp_path_vec(coords, self.hero)
            ref_vec = exit_compass._comp_sum_vec(hero_portal_vec, self.hero_rel_pos)
            exit_compass.add_ref_vec(
                source=self.hero_start_image,
                dest=dest,
                ref_vec=ref_vec
            )
        exit_compass.print_dict()

        if self.board.previous_board:
            print("board shifted:\t", self.board.board_shifted)

        # Get battlefield information
        self.actionspace = self.board.get_actionspace()

    def act_state(self) -> Tuple[int, int, int]:
        """ set state if none and return top state action """

        if not self.stateStack:  # If state is None - choose another one
            if self.board.nearest_gold:
                self.append_stack("GOLD")
            elif self.board.nearest_dead_player:
                self.append_stack("LOOT")
            elif True:
                self.append_stack("EXIT")
            elif self.board.nearest_transition:
                self.append_stack("EXPLORE")

        return self.state_methods[self.stateStack[-1].code]()

    def append_stack(self, state_name: str,
                     goal: Tuple[int, int] = None) -> None:
        """ add new state on a top of a stack """

        if state_name in BotStateMachine.states:
            self.stateStack.append(
                State(BotStateMachine.states[state_name], goal=goal))
        else:
            raise Exception(f"Tring to append non excisting {state_name} to stateStack")

    def shift_stack(self) -> None:
        correct_state = []
        for i in range(len(self.stateStack)):
            state = self.stateStack[i]
            if not state.shift_coord(self.shift_direction):
                correct_state.append(state)
        self.stateStack = correct_state

    def _cmd_to_action(self,
                       action: Tuple[int, int, int]) -> Tuple[str, Tuple[int, int]]:
        """ transforms coordinates and action code to server command """
        print("action: ", action)
        if not action:
            return "", (0, 0)

        cmd_dir = ""
        hero = self.hero

        # Jump on my place
        if action[:2] == hero[:2]:
            if action[2] == 1:
                return "ACT(1)", (0, 0)
            elif action[2] == -1:
                return "", (0, 0)
        shift = (0, 0)
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
        # bord shift is in opposite direction then player move
        shift = (shift[1], shift[0])
        return cmd_prefix + cmd_dir, shift

    def _check_jump(self, dest: Tuple[int, int]) -> bool:
        """ check if passed coordinates need jump to reach it """

        return abs((dest[0] - self.hero[0]) + (dest[1] - self.hero[1])) > 1

    def _check_shoot(self) -> bool:
        """ check if passed recoil time """

        return self.firingTimer == 0

    def _next_move_calculation(self, state: State) -> Tuple[int, int, int]:
        """ check plannedPath and get next move """

        print("state Goal: ", state.stateGoal)
        if not state.plannedPath:
            state.plannedPath = self.board.astar(self.hero, state.stateGoal)
        print("state plannedPath: ", state.plannedPath)
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
        if (*next_node, code) in self.actionspace:
            return next_move  # If it`s safe - act as planned
        else:
            # If it`s unsafe - dodge
            self.append_stack("DODGE", goal=state.stateGoal)
            return self.act_state()

    """
    STATES FUNCTIONS
    """

    @state_control
    def _rebirth(self) -> Tuple:
        """ if we are dead, reset else standing on exit, try to shoot """

        # TODO check if we can kill anyone
        # Reset all stuff
        self.__init__()
        return ()

    @state_control
    def _exit(self) -> Tuple[int, int, int]:
        """ searching for exit """

        state = self.stateStack[-1]

        if state.check_goal(self.hero):  # If the exit is reached, rebirth
            self.append_stack("REBIRTH")
            return self.act_state()
        if not state.stateGoal:
            nearest_exit = exit_compass.calc_vec(
                start=self.hero_start_image,
                rel_pos=self.hero_rel_pos)
            print("nearest_exit: ", nearest_exit)

            if not nearest_exit:
                # Leave the state, if there`s no exits
                self.append_stack("EXPLORE")
                return self.act_state()
            else:
                nearest_hero_exit = (self.hero[0] + nearest_exit[0],
                                     self.hero[1] + nearest_exit[1])
                print("nearest_hero_exit: ", nearest_hero_exit)

            if not(0 <= nearest_hero_exit[0] <= 19 and 0 <= nearest_hero_exit[1] <= 19):
                shortest_path = float("inf")
                nearest_transition = None
                for transition in self.board.get_edge_transitions():
                    exit_path = (nearest_hero_exit[0] - transition[0],
                                 nearest_hero_exit[1] - transition[1])
                    manh_path = exit_path[0] ** 2 + exit_path[1] ** 2
                    if manh_path < shortest_path:
                        shortest_path = manh_path
                        nearest_transition = transition
                state.stateGoal = nearest_transition
            else:
                state.stateGoal = nearest_hero_exit
        return self._next_move_calculation(state)

    @state_control
    def _gold(self) -> Tuple[int, int, int]:
        """ searching for gold """

        state = self.stateStack[-1]

        if self.board.collected_gold():
            self.goldCollected += 1
            state.reset()

        if self.board.final_level and self.goldCollected > 2:
            self.append_stack("EXIT")
            return self.act_state()

        if not self.board.golds:  # check if gold exists
            self.stateStack.pop()
            return self.act_state()
        else:
            if state.stateGoal not in self.board.golds and self.board.nearest_gold:
                # This is called when we pick the gold we looked for
                state.stateGoal = self.board.nearest_gold
            return self._next_move_calculation(state)

    @state_control
    def _dodge(self):
        """ find action nearest to target by manhetan distance """

        state = self.stateStack[-1]
        target = state.stateGoal
        self.stateStack[-2].dropPath()  # previous_state
        self.stateStack.pop()

        lowest_dist = float("inf")
        optimal_move = None
        for action in self.actionspace:
            dist = self.board._mht_dist(action[:2], target)
            if dist < lowest_dist:
                lowest_dist = dist
                optimal_move = action
        return optimal_move

    @state_control
    def _passive_hunt(self):
        """ attack if we are safe """

        self.stateStack.pop()

        if ((*self.hero, -1) not in self.actionspace) or (not self._check_shoot()):
            return self.act_state()
        else:
            target = self.board._targets[0]
            self.firingTimer = BotStateMachine.gunRecharge
            return (*target, 3)

    @state_control
    def _active_hunt(self):
        # TODO kill anyone on this field
        pass

    @state_control
    def _jump(self):
        """ do nothing in jump """

        self.stateStack.pop()
        return ()

    @state_control
    def _loot(self):
        """ loot on dead players """

        state = self.stateStack[-1]
        state.stateGoal = self.board.nearest_dead_player
        step_toward_loot = self._next_move_calculation(state)
        self.stateStack.pop()
        return step_toward_loot

    @state_control
    def _explore(self):
        """ explore map adges """

        state = self.stateStack[-1]
        if not state.stateGoal:
            state.stateGoal = self.board.nearest_transition
        return self._next_move_calculation(state)
