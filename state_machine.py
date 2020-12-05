from typing import Tuple, List
from functools import wraps

from board import Board, mht_dist


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
            raise Exception(f"Trying to execute <{func_name}> in <{state_name}> state")
        func(self, *args, **kwargs)
    return wrapper


class State():
    def __init__(self, code: int, goal: Tuple[int,int] = None):
        self.code = code  # BotStateMachine.states index
        #Priority states cannot be switched
        self.priority = False
        # State may or may not have a goal and planned path
        # e.g Walk to exit has one, dodge doesnt
        self.stateGoal: Tuple[int, int] = goal
        self.plannedPath: List[tuple[int, int]] = None

    def pop_path_node(self, skip:Tuple[int, int] = None) -> Tuple[int, int]:
        if not self.plannedPath:
            raise "no plannedPath"
        next_node = self.plannedPath.pop(0)
        if next_node == skip:
            if not self.plannedPath:
                raise "no fearther plannedPath"
            next_node = self.plannedPath.pop(0)
        return next_node

    def check_goal(self, check_coords:Tuple[int, int]) -> bool:
        """ are we already on our target coordinate """
        return check_coords == self.stateGoal

    def reset(self) -> None:
        self.priority = False
        self.stateGoal = None
        self.plannedPath = None

    def dropPath(self) -> None:
        self.plannedPath = None

    def __str__(self) -> str:
        return f"State #{self.code}" + f"Goal: {self.stateGoal}" if self.stateGoal else ''


class BotStateMachine():
    # control variables
    shotRecoil = 3

    # DEATH - Resets all 
    states = {
        "REBIRTH":0,
        "EXIT":1,
        "GOLD":2,
        "ACTIVE_HUNT":3,
        "PASSIVE_HUNT":4,
        "DODGE":5,
    }

    def __init__(self, ):
        # Initialize state_methods
        self.state_methods = (
            self._rebirth,
            self._exit,
            self._gold,
            self._active_hunt,
            self._passive_hunt,
            self._dodge
        )
        self.state_methods_names = list(func.__name__ for func in self.state_methods)

        # Initialize ❤️ base player state
        self.firingTimer = 0
        self.goldCollected = 0
        self.activeBonus=None
        self.bonusTerm=0
        #In state-goal stack states are stored with goals
        self.stateStack: List[State] = []

        #For a test, add a movement state to the stack
        self.stateStack.append(State(BotStateMachine.states["GOLD"]))

    def yield_decision(self, board:Board):
        #Get battlefield information
        self.board = board
        self.hero = self.board._hero
        self.exits = set(self.board.get_exits())
        self.golds = set(self.board.get_golds())
        self.actionspace = self.board.get_actionspace() # Returns possible and save actions

        # Force rebirth if killed
        if not self.board.is_me_alive():
            self.stateStack.append(State(BotStateMachine.states["REBIRTH"]))

        self.stateStack.append(State(BotStateMachine.states["REBIRTH"]))
        self._exit()
        exit()
        # Passive hunt
        # if not self.stateStack[-1].priority:
        #     self.stateStack.append(State(BotStateMachine.states["PASSIVE_HUNT"]))

        cmd = self.act_state()
   
        if not cmd:
            return ''
        return self._cmd_to_action(cmd)

    def act_state(self) -> Tuple[int, int, int]:  # result of state decision
        """ set state if none and return top state action """
        
        
        if not self.stateStack:  # If state is None - choose another one
            # TODO Implement a state searcher if out of all states, currently march to exits
            self.stateStack.append(State(BotStateMachine.states["EXIT"]))
            
        return self.state_methods[self.stateStack[-1].code]()

    def _cmd_to_action(self, action: Tuple[int, int, int]) -> str:
        """ transforms coordinates and action code to server command """
        
        cmd_dir = ''
        hero = self.hero

        #Jump on my place
        if action[2] == 1 and action[0] == hero[0] and action[1] == hero[1]:
            return 'ACT(1)'

        if hero[0] > action[0]:
            cmd_dir = 'LEFT'
        elif hero[0] < action[0]:
            cmd_dir = 'RIGHT'
        elif hero[1] > action[1]:
            cmd_dir = 'UP'
        elif hero[1] < action[1]:
            cmd_dir = 'DOWN'

        cmd_code = action[2]
        cmd_prefix = ''
        if cmd_code in (1,2,3):
            cmd_prefix += f'ACT({cmd_code}),'

        return cmd_prefix + cmd_dir

    def _check_jump(self, dest):
        hero = self.hero
        return abs(dest[0]-hero[0]) == 2 or abs(dest[1]-hero[1]) == 2

    def _next_move_calculation(self, state: State) -> Tuple[int, int, int]:
        """ check path and get next move """
        
        if not state.plannedPath:
            state.plannedPath =  self.board.astar(self.hero, state.stateGoal)

        next_node = state.pop_path_node(skip=self.hero)

        if next_node:
            if self._check_jump(next_node):
                code = 1  # jump code
            else:
                code = -1  # ignore code for walk
            next_move = (*next_node, code)
        else:
            raise "no next_node to use"
        
        # Make sure it`s safe
        if next_move in self.actionspace:
            return next_move  # If it`s safe - act as planned
        else:
            # If it`s unsafe - dodge
            self.stateStack.append(State(BotStateMachine.states["DODGE"],
                                         goal=state.stateGoal))
            return self.act_state()



    @state_control
    def _rebirth(self) -> str:
        # TODO check if we can kill anyone
        # Reset all stuff
        self.__init__()
        return ''
    
    @state_control
    def _exit(self) -> Tuple[int, int, int]:
        state = self.stateStack[-1]
        
        hero = self.hero
        exits = self.exits

        if exits:

            if not state.stateGoal:  # check if we have goal
                state.stateGoal = self.board.bfs_nearest(hero, exits)  # find nearest exit
                if not state.stateGoal:  # no exit avaliable search another stuff
                    self.stateStack.pop()
                    return self.act_state()

            if state.check_goal(hero):
                # If the exit is reached, rebirth
                self.stateStack.append(State(BotStateMachine.states["REBIRTH"]))
                return self.act_state()

            return self._next_move_calculation(state)

        else:
            # Leave the state, if there`s no exits
            self.stateStack.pop()
            return self.act_state()

    @state_control
    def _gold(self) -> Tuple[int, int, int]:
        state = self.stateStack[-1]

        hero = self.hero
        golds = self.golds
        cmd = None

        if golds:
            # TODO check if gold exists
            # This is called when we pick the gold we looked for,
            # but there`s gold on the map elsewhre
            if state.check_goal(hero):
                state.reset()

            if not state.stateGoal:
                state.stateGoal = self.board.bfs_nearest(hero, golds)
                if not state.stateGoal:  # no golds avaliable search another stuff
                    self.stateStack.pop()
                    return self.act_state()

            return self._next_move_calculation(state)
        else:
            #Check for non state-exit stuff, e.g zombie on a gold bag
            self.stateStack.pop()
            return self.act_state()
    
    @state_control
    def _dodge(self):
        state = self.stateStack[-1]
        state.stateGoal
        self.actionspace
        # TODO find safe path by manhattan
        pass
    
    @state_control
    def _passive_hunt(self):
        # TODO check sanity of attack
        pass
    
    @state_control
    def _active_hunt(self):
        # TODO kill anyone on this field
        pass
