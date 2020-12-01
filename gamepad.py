from inputs import get_gamepad
from colorama import init, Fore
init(autoreset=True)
from time import sleep
from threading import Thread

_COMMANDS = dict(
    DIE="ACT(0)",

    LEFT="LEFT",
    RIGHT="RIGHT",
    UP="UP",
    DOWN="DOWN",

    JUMP="ACT(1)",
    JUMP_LEFT="ACT(1),LEFT",
    JUMP_RIGHT="ACT(1),RIGHT",
    JUMP_UP="ACT(1),UP",
    JUMP_DOWN="ACT(1),DOWN",

    PULL_LEFT="ACT(2),LEFT",
    PULL_RIGHT="ACT(2),RIGHT",
    PULL_UP="ACT(2),UP",
    PULL_DOWN="ACT(2),DOWN",

    FIRE_LEFT="ACT(3),LEFT",
    FIRE_RIGHT="ACT(3),RIGHT",
    FIRE_UP="ACT(3),UP",
    FIRE_DOWN="ACT(3),DOWN",

    NULL=""
)

class GamepadRoboController():

    def __init__(self):
        self.firing_hold = 0
        self.jump_hold = 0
        self.grab_hold = 0
        self.last_direction = "UP"
        self.move = 0
        t = Thread(target=self.g_ask)
        t.start()
    
    def btn_act(self, btn, value):
        if btn == "BTN_SOUTH":
            self.firing_hold = value
        elif btn == "BTN_NORTH":
            self.jump_hold = value
        elif btn == "BTN_WEST":
            self.grab_hold = value
        #print([self.firing_hold, self.jump_hold, self.grab_hold])
        
    def dir_act(self, axis, value):
        if value != 0:
            self.move = 1
            if axis == "ABS_HAT0Y":
                # Save last direction
                self.last_direction = "DOWN" if value == 1 else "UP" if value == -1 else self.last_direction
            elif axis == "ABS_HAT0X":
                self.last_direction = "RIGHT" if value == 1 else "LEFT" if value == -1 else self.last_direction 
        #print([self.last_direction, self.move])

    def g_ask(self):
        while True:
            self.get_gamepad_action()

    def get_action_code(self):
        n = 0
        if self.firing_hold:
            n = 3
        elif self.grab_hold:
            n = 2
        elif self.jump_hold:
            n = 1

        if n!=0:
            # return if action commited
            self.move = 0
            return f"ACT({n})," + self.last_direction
        elif self.move:
            self.move = 0
            return self.last_direction
        else:
            return ""

    def get_gamepad_action(self):
        events = get_gamepad()
        for event in events:
            #print(event.code, event.state)
            if event.ev_type == "Key":
                self.btn_act(event.code, event.state)
            if event.ev_type == "Absolute":
                self.dir_act(event.code, event.state)
    




if __name__ == "__main__":
    print("running as main")
    gp = GamepadRoboController()
    while True:
        sleep(1)
        print(gp.get_action_code())
