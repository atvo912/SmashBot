import melee
import Tactics
from melee.enums import Action, Button
from Chains.chain import Chain
from enum import Enum
#from Tactics.tactic import Tactic
#from Tactics.punish import Punish

class TILT_DIRECTION(Enum): #consider adding possibilities for angled tilts and turnaround tilts
    UP = 0
    DOWN = 1
    FORWARD = 2
    BACK = 3
    NEUTRAL = 4 #neutral tilt = jab
    TURNAROUND = 5

class TiltAttack(Chain):
    def __init__(self, direction=TILT_DIRECTION.UP):
        #self.charge = charge #not valid for tilts
        self.direction = direction

    def step(self, gamestate, smashbot_state, opponent_state):
        controller = self.controller

        tiltablestates = [Action.STANDING, Action.WALK_SLOW, Action.WALK_MIDDLE, \
            Action.WALK_FAST, Action.EDGE_TEETERING_START, Action.EDGE_TEETERING, Action.CROUCHING, Action.CROUCH_START, Action.CROUCH_END]

        if smashbot_state.action == Action.LANDING_SPECIAL: #might need to add more action states here
            self.interruptible = True
            controller.empty_input()
            return

        if smashbot_state.action == Action.RUNNING: #hit down to run cancel
            self.interruptible = True
            controller.tilt_analog(Button.BUTTON_MAIN, .5, 0)
            return

        # Do we need to jump cancel? #Jump canceling isn't valid for tilts
        #jumpcancelactions = [Action.SHIELD, Action.SHIELD_RELEASE, Action.DASHING, Action.RUNNING]
        #if smashbot_state.action in jumpcancelactions:
            #self.interruptible = False
            #controller.press_button(Button.BUTTON_Y)
            #return

        # Jump out of shine #Jump canceling isn't valid for tilts
        #isInShineStart = (smashbot_state.action == Action.DOWN_B_STUN or \
            #smashbot_state.action == Action.DOWN_B_GROUND_START or \
            #smashbot_state.action == Action.DOWN_B_GROUND)
        #if isInShineStart and smashbot_state.action_frame >= 3 and smashbot_state.on_ground:
            #self.interruptible = False
            #controller.press_button(Button.BUTTON_Y)
            #return

        #this should not matter at all
        #if smashbot_state.action in [Action.FSMASH_MID, Action.UPSMASH, Action.DOWNSMASH]:
            # Are we in the early stages of the smash and need to charge?
            #if self.frames_charged < self.charge:
                #self.interruptible = False
                #self.frames_charged += 1
                #controller.press_button(Button.BUTTON_A)
                #return
            # Are we done with a smash and just need to quit?
            #else:
                 #self.interruptible = True
                 #controller.empty_input()
                 #return

        # Let go of A if we were already pressing A
        if controller.prev.button[Button.BUTTON_A]:
            controller.empty_input()
            self.interruptible = True
            return

        # Pivot. You can't shine from a dash animation. So make it a pivot
        if smashbot_state.action == Action.DASHING:
            # Turn around
            self.interruptible = True
            controller.release_button(Button.BUTTON_A)
            controller.tilt_analog(Button.BUTTON_MAIN, int(not smashbot_state.facing), .5)
            return

        #We need to input a jump to wavedash out of these states if dash/run gets called while in one of these states, or else we get stuck
        #jcstates = [Action.DASHING]
        #if (smashbot_state.action in jcstates):
                #self.controller.press_button(Button.BUTTON_Y)
                #return

        # Airdodge for the wavedash
        #jumping = [Action.JUMPING_ARIAL_FORWARD, Action.JUMPING_ARIAL_BACKWARD]
        #jumpcancel = (smashbot_state.action == Action.KNEE_BEND) and (smashbot_state.action_frame == 3)
        #if jumpcancel or smashbot_state.action in jumping:
            #self.controller.press_button(Button.BUTTON_L)
            #onleft = smashbot_state.x < endposition #don't know how to call endposition here
            # Normalize distance from (0->1) to (0.5 -> 1)
            #x = 1
            #if onleft != True:
                #x = -x
            #self.controller.tilt_analog(Button.BUTTON_MAIN, x, 0.35)
            #return

        #Complete the pivot -- This block may be unnecessary if Fox can just tilt during Action.TURNING no matter what, he can't during tilt turn.
        #if smashbot_state.action == Action.TURNING:
            #controller.empty_input()
            #self.interruptible = True
            #return


        self.interruptible = True




        if (smashbot_state.action in tiltablestates) or (smashbot_state.action == Action.TURNING):
            if self.direction == TILT_DIRECTION.TURNAROUND:
                if smashbot_state.action == Action.TURNING and smashbot_state.action_frame == 1: #frame 1 of smash turn is weird
                    return
                else:
                    if smashbot_state.facing: #turn to the left if facing right
                        controller.tilt_analog(Button.BUTTON_MAIN, 0, .5)
                    else: #turn right otherwise
                        controller.tilt_analog(Button.BUTTON_MAIN, 1, .5)
                controller.release_button(Button.BUTTON_A)
            else:
                controller.press_button(Button.BUTTON_A)
                if self.direction == TILT_DIRECTION.UP:
                    controller.tilt_analog(Button.BUTTON_MAIN, .5, 0.7)
                elif self.direction == TILT_DIRECTION.DOWN:
                    controller.tilt_analog(Button.BUTTON_MAIN, .5, 0.3)
                elif self.direction == TILT_DIRECTION.FORWARD:
                    if smashbot_state.facing: #ftilt to the right if facing right
                        controller.tilt_analog(Button.BUTTON_MAIN, 0.7, .5)
                    else: #ftilt left otherwise
                        controller.tilt_analog(Button.BUTTON_MAIN, 0.3, .5)
                elif self.direction == TILT_DIRECTION.BACK:
                    controller.tilt_analog(Button.BUTTON_MAIN, int(not smashbot_state.facing), .5) #this has not been modified to not fsmash yet
                elif self.direction == TILT_DIRECTION.NEUTRAL:
                    controller.tilt_analog(Button.BUTTON_MAIN, .5, .5) #neutral tilt = jab
                #elif self.direction == TILT_DIRECTION.TURNAROUND: #THIS DOES NOT WORK YET
                    #if smashbot_state.facing: #utilt to the left if facing right
                    #    controller.tilt_analog(Button.BUTTON_MAIN, 0.41, .7)
                    #else: #utilt right otherwise
                    #    controller.tilt_analog(Button.BUTTON_MAIN, 0.59, .7)
                    #if smashbot_state.action == Action.TURNING and smashbot_state.action_frame == 1: #frame 1 of smash turn is weird
                    #return
                    #else:
                        #if smashbot_state.facing: #turn to the left if facing right
                            #controller.tilt_analog(Button.BUTTON_MAIN, 0, .5)
                        #else: #turn right otherwise
                            #controller.tilt_analog(Button.BUTTON_MAIN, 1, .5)
                    #controller.release_button(Button.BUTTON_A)
                    #controller.tilt_analog(Button.BUTTON_MAIN, 0.4, .5)
