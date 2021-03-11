import melee
from melee.enums import Action, Button
from Chains.chain import Chain
from enum import Enum

class MULTISHINE_DIRECTION(Enum):
    NEUTRAL = 1
    FORWARD = 2
    BACK = 3

class Multishine(Chain):
    def __init__(self, direction = MULTISHINE_DIRECTION.FORWARD):
        self.direction = direction

    def step(self, gamestate, smashbot_state, opponent_state):
        controller = self.controller

        actionable_landing = smashbot_state.action == Action.LANDING and smashbot_state.action_frame >= 4

        #If standing or turning, shine
        if smashbot_state.action in [Action.STANDING, Action.TURNING] or actionable_landing:
            controller.press_button(Button.BUTTON_B)
            controller.tilt_analog(Button.BUTTON_MAIN, .5, 0)
            self.interruptible = False
            return

        #Shine on frame 3 of knee bend, else nothing
        if smashbot_state.action == Action.KNEE_BEND:
            if smashbot_state.action_frame == 3:
                controller.press_button(Button.BUTTON_B)
                controller.tilt_analog(Button.BUTTON_MAIN, .5, 0)
                self.interruptible = False
                return
            if smashbot_state.action_frame == 2:
                self.interruptible = False
                if self.direction == MULTISHINE_DIRECTION.FORWARD:
                    controller.tilt_analog(Button.BUTTON_MAIN, int(smashbot_state.facing), .5) #advancing JC shine
                elif self.direction == MULTISHINE_DIRECTION.BACK:
                    controller.tilt_analog(Button.BUTTON_MAIN, int(not smashbot_state.facing), .5) #retreating JC shine
                else:
                    controller.empty_input()
                return
            if smashbot_state.action_frame == 1:
                self.interruptible = True
                controller.empty_input()
                return

        isInShineStart = (smashbot_state.action == Action.DOWN_B_STUN or \
            smashbot_state.action == Action.DOWN_B_GROUND_START or \
            smashbot_state.action == Action.DOWN_B_GROUND)

        #Jump out of shine
        if isInShineStart and smashbot_state.action_frame >= 3 and smashbot_state.on_ground:
            controller.press_button(Button.BUTTON_Y)
            self.interruptible = False
            return

        if smashbot_state.action == Action.DOWN_B_GROUND:
            controller.press_button(Button.BUTTON_Y)
            self.interruptible = False
            return

        # Catchall
        self.interruptible = True
        controller.empty_input()
