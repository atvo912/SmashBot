import melee
import random
from Chains.chain import Chain
from melee.enums import Action, Button

class DashDance(Chain):
    def __init__(self, pivot, radius=0):
        self.pivotpoint = pivot
        self.radius = radius
        self.interruptible = True

    def step(self, gamestate, smashbot_state, opponent_state):
        #TODO: Moonwalk protection
        if smashbot_state.moonwalkwarning and self.controller.prev.main_stick[0] != 0.5:
            self.controller.empty_input()
            return

        # Causes an empty_input if hitting right did not cause Smashbot to be TURNING or DASHING right.
        if (self.controller.prev.main_stick[0] == 1) and (smashbot_state.action == Action.DASHING and not smashbot_state.facing):
            self.controller.empty_input()
            return

        # Causes an empty_input if hitting left did not cause Smashbot to be TURNING or DASHING left.
        if (self.controller.prev.main_stick[0] == 0) and (smashbot_state.action == Action.DASHING and smashbot_state.facing):
            self.controller.empty_input()
            return


        if smashbot_state.action == Action.ON_HALO_WAIT:
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 0.5, 0)
            return

        if smashbot_state.action in [Action.LYING_GROUND_UP, Action.LYING_GROUND_DOWN]:
            roll = random.randint(0, 3)
            if roll <= 1:
                self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 0.5, 1)
                return
            elif roll == 2:
                self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 1, 0.5)
                return
            else:
                self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 0, 0.5)
                return

        # If we're in spotdodge or shield, do nothing
        if smashbot_state.action in [Action.SPOTDODGE, Action.SHIELD_RELEASE]:
            self.controller.empty_input()
            return

        # If we're stuck wavedashing, just hang out and do nothing
        if smashbot_state.action == Action.LANDING_SPECIAL and smashbot_state.action_frame < 28:
            self.controller.empty_input()
            return

        #If we're walking, stop for a frame
        #Also, if we're shielding, don't try to dash. We will accidentally roll
        if smashbot_state.action == Action.WALK_SLOW or \
            smashbot_state.action == Action.WALK_MIDDLE or \
            smashbot_state.action == Action.WALK_FAST or \
            smashbot_state.action == Action.SHIELD_START or \
            smashbot_state.action == Action.SHIELD_REFLECT or \
            smashbot_state.action == Action.SHIELD:
                self.controller.empty_input()
                return

        #If we're starting the turn around animation, keep pressing that way or
        #   else we'll get stuck in the slow turnaround
        if smashbot_state.action == Action.TURNING and smashbot_state.action_frame == 1:
            return

        #Dash back, since we're about to start running
        # #Action.FOX_DASH_FRAMES
        if smashbot_state.action == Action.DASHING and smashbot_state.action_frame >= 11:
                self.controller.tilt_analog(melee.Button.BUTTON_MAIN, int(not smashbot_state.facing), .5)
                return

        #Hit down to run cancel if you enter Action.RUNNING, continue holding down if in CROUCH_START
        # #Action.FOX_DASH_FRAMES
        if smashbot_state.action == Action.RUNNING or smashbot_state.action == Action.RUN_BRAKE or smashbot_state.action == Action.CROUCH_START:
                self.controller.tilt_analog(melee.Button.BUTTON_MAIN, .5, 0)
                return

        #We can't dashback while in CROUCH_END. We can, however, dash forward.
        if smashbot_state.action == Action.CROUCH_END:
                self.controller.tilt_analog(melee.Button.BUTTON_MAIN, int(smashbot_state.facing), 0)
                return

        #We need to input a jump to wavedash out of these states if dash/run gets called while in one of these states, or else we get stuck
        jcstates = [Action.DOWN_B_GROUND_START, Action.DOWN_B_GROUND]
        if (smashbot_state.action in jcstates) or (smashbot_state.action == Action.TURNING and smashbot_state.action_frame in range(2,12)): #detects accidental tilt turns
                self.controller.press_button(Button.BUTTON_Y)
                return

        # Airdodge for the wavedash
        jumping = [Action.JUMPING_ARIAL_FORWARD, Action.JUMPING_ARIAL_BACKWARD]
        jumpcancel = (smashbot_state.action == Action.KNEE_BEND) and (smashbot_state.action_frame == 3)
        if jumpcancel or smashbot_state.action in jumping:
            self.controller.press_button(Button.BUTTON_L)
            onleft = smashbot_state.x < opponent_state.x
            # Normalize distance from (0->1) to (0.5 -> 1)
            x = 1
            if onleft != False:
                x = -x
            self.controller.tilt_analog(Button.BUTTON_MAIN, x, 0.35)
            return

        #We can't dash IMMEDIATELY after landing. So just chill for a bit #This was changed from 2 to 4
        if (smashbot_state.action == Action.LANDING and smashbot_state.action_frame < 4) or \
            not smashbot_state.on_ground:
                self.controller.empty_input()
                return

        #Don't run off the stage
        if abs(smashbot_state.x) > \
            melee.stages.edgegroundposition(gamestate.stage) - 6.6:#(3 * FOX_DASH_SPEED):
                x = 0
                if smashbot_state.x < 0:
                    x = 1
                self.controller.tilt_analog(melee.Button.BUTTON_MAIN, x, .5)
                return

        #Are we outside the given radius of dash dancing?
        if smashbot_state.x < self.pivotpoint - self.radius:
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 1, .5)
            return

        if smashbot_state.x > self.pivotpoint + self.radius:
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 0, .5)
            return

        #Dash away if within a given radius
        self.controller.tilt_analog(melee.Button.BUTTON_MAIN, int(not smashbot_state.facing), .5)
        return
