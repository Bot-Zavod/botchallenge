from typing import Tuple, List
from board import Board, mht_dist

class State():
    def __init__(self, code: int):
        self.code = code
        #Priority states cannot be switched
        self.priority = False
        # State may or may not have a goal and planned path
        # e.g Walk to exit has one, dodge doesnt
        self.stateGoal: Tuple[int:int] = None
        self.plannedPath: List[tuple[int:int]] = None

    def pop_path_node(self, skip:Tuple[int, int] = None):
        if not self.plannedPath:
            return None
        next_node = self.plannedPath.pop(0)
        if next_node == skip:
            if not self.plannedPath:
                return None
            next_node = self.plannedPath.pop(0)
        return next_node

    def check_goal(self, check_coords):
        return check_coords == self.stateGoal

    def reset(self):
        self.priority = False
        self.stateGoal = None
        self.plannedPath = None

    def dropPath(self):
        self.plannedPath = None

    def __str__(self):
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
        self.state_methods = (self._rebirth, self._exit, self._gold)

        # Initialize ❤️ base player state
        self.firingTimer = 0
        self.goldCollected = 0
        self.activeBonus=None
        self.bonusTerm=0
        #In state-goal stack states are stored with goals
        self.stateStack: State = []

        #For a test, add a movement state to the stack
        self.stateStack.append(State(BotStateMachine.states["GOLD"]))

    def yield_decision(self, board:Board):
        #Get battlefield information
        self.board = board
        self.hero = self.board.get_hero()
            #Hero should have a state

        #Force rebirth if killed
        if not self.board.is_me_alive():
            self.stateStack.append(State(BotStateMachine.states["REBIRTH"]))

        #If we are in any legit state - act
        cmd = self.act_state()
   
        #Passive hunt

        # If it`s safe - act as planned

        # If state is none - choose another one
        # Make sure it`s safe
        # If it`s unsafe - override
        # If it`s unsafe - dodge

        # cmd = self._exit()
        if not cmd:
            return ''
        return self._cmd_to_action(cmd)
        # return self._cmd_to_action((10,10,3))

    def act_state(self):
        if self.stateStack:
            return self.state_methods[self.stateStack[-1].code]()
        else:
            #TODO Implement a state searcher if out of all states, currently march to exits
            self.stateStack.append(State(BotStateMachine.states["EXIT"]))
            return self.state_methods[self.stateStack[-1].code]()
            print('Trying to act without an active state') 

    def _cmd_to_action(self, action:Tuple[int, int, int]):
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

    def _rebirth(self):
        # Reset all stuff
        self.__init__()
        return ''

    def _exit(self):
        state = None
        #Check if there is an exit command
        if not self.stateStack[-1].code == BotStateMachine.states["EXIT"]:
            print("Trying to execute wrong state (Exit)")
        else:
            state = self.stateStack[-1]
        
        hero = self.hero
        exits = set(self.board.get_exits())

        if exits:

            if not state.stateGoal:
                state.stateGoal = self.board.bfs_nearest(hero, exits)
                #TODO Get out of this state if the exit is unreachable

            if state.check_goal(hero):
                #If the exit is reached, rebirth
                print("REBIRTH")
                self.stateStack.append(State(BotStateMachine.states["REBIRTH"]))
                return self.act_state()

            if not state.plannedPath:
                state.plannedPath =  self.board.astar(hero, state.stateGoal)

            next_node = state.pop_path_node(skip = hero)

            if next_node:
                return ((*next_node, 1 if self._check_jump(next_node) else -1))

        else:
            #Leave the state, if there`s no exits
            self.stateStack.pop()
            return self.act_state()

    def _gold(self):
        state = None
        #Check if there is LOOK for gold command
        if not self.stateStack[-1].code == BotStateMachine.states["GOLD"]:
            print("Trying to execute wrong state (Gold)")
        else:
            state = self.stateStack[-1]

        hero = self.hero
        golds = set(self.board.get_golds())
        cmd = None

        if golds: 
            #This is called when we pick the gold we looked for, but there`s gold on the map elsewhre
            if state.check_goal(hero):
                state.reset()

            if not state.stateGoal:
                state.stateGoal = self.board.bfs_nearest(hero, golds)
                #TODO Get out of this state if no gold in reach unreachable

            if not state.plannedPath:
                state.plannedPath =  self.board.astar(hero, state.stateGoal)

            next_node = state.pop_path_node(skip = hero)

            if next_node:
                return ((*next_node, 1 if self._check_jump(next_node) else -1))
        else:
            #Check for non state-exit stuff, e.g zombie on a gold bag
            self.stateStack.pop()
            return self.act_state()





