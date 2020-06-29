import melee
from melee.enums import Action, Button
from Chains.chain import Chain
from enum import Enum

class THROW_DIRECTION(Enum):
    UP = 0
    DOWN = 1
    FORWARD = 2
    BACK = 3

# Grab and throw opponent
class GrabAndThrow(Chain):
    def __init__(self, direction=THROW_DIRECTION.DOWN):
        self.direction = direction

    def step(self, gamestate, smashbot_state, opponent_state):
        controller = self.controller

        self.interruptible = False

        # If we already pressed Z last frame, let go
        if controller.prev.button[Button.BUTTON_L]:
            controller.empty_input()
            return

        if smashbot_state.action == Action.GRAB and smashbot_state.action_frame > 12:
            controller.empty_input()
            self.interruptible = True
            return

        if smashbot_state.action == Action.LANDING_SPECIAL:
            controller.empty_input()
            self.interruptible = True
            return

        # If we need to jump cancel, do it
        jcstates = [Action.DOWN_B_GROUND_START, Action.DOWN_B_GROUND, Action.SHIELD, Action.SHIELD_RELEASE, Action.SHIELD_START, Action.DASHING, Action.RUNNING, Action.RUN_BRAKE,  Action.CROUCH_START, Action.CROUCH_END, Action.CROUCHING] #added more action states
        if (smashbot_state.action in jcstates) and smashbot_state.action_frame >= 3:
            controller.press_button(Button.BUTTON_Y)
            if controller.prev.button[Button.BUTTON_Y]:
                controller.press_button(Button.BUTTON_X) #press X if Y is already held
                return
            controller.release_button(Button.BUTTON_Z)
            return

        # Grab on knee bend
        if smashbot_state.action == Action.KNEE_BEND:
            # Let go of Z if we already had it pressed
            if controller.prev.button[Button.BUTTON_Z]:
                controller.release_button(Button.BUTTON_Z)
                return
            controller.press_button(Button.BUTTON_Z)
            return

        # Do the throw
        if smashbot_state.action == Action.GRAB_WAIT or smashbot_state == Action.GRAB_PULLING:
            if self.direction == THROW_DIRECTION.DOWN:
                controller.tilt_analog(Button.BUTTON_MAIN, .5, 0)
            if self.direction == THROW_DIRECTION.UP:
                controller.tilt_analog(Button.BUTTON_MAIN, .5, 1)
            if self.direction == THROW_DIRECTION.FORWARD:
                controller.tilt_analog(Button.BUTTON_MAIN, int(smashbot_state.facing), .5)
            if self.direction == THROW_DIRECTION.BACK:
                controller.tilt_analog(Button.BUTTON_MAIN, int(not smashbot_state.facing), .5)
            self.interruptible = True
            return

        # Do the grab
        # Let go of Z if we already had it pressed
        if controller.prev.button[Button.BUTTON_Z]:
            controller.release_button(Button.BUTTON_Z)
            return
        grabstates = [Action.GRAB_WAIT, Action.GRAB_PULLING, Action.GRAB_PUMMEL]
        if smashbot_state.action not in grabstates and smashbot_state.action not in jcstates: #prevents getting stuck in infinite pummel loop
            controller.press_button(Button.BUTTON_Z)
