import melee
from melee.enums import Action, Button
from Chains.chain import Chain

class Multishine(Chain):
    def step(self, gamestate, smashbot_state, opponent_state):
        controller = self.controller

        #If standing or turning, shine
        # Should add various crouch states here too, along with RUNNING/RUNBRAKE
        if smashbot_state.action == Action.STANDING or smashbot_state.action == Action.TURNING:
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
                controller.tilt_analog(Button.BUTTON_MAIN, int(smashbot_state.facing), .5) #advancing JC shine
                #controller.empty_input() #removed for advancing JC shine
                return
            if smashbot_state.action_frame == 1:
                self.interruptible = True
                #controller.tilt_analog(Button.BUTTON_MAIN, int(smashbot_state.facing), .5) #advancing JC shine
                controller.empty_input() #removed for advancing JC shine
                return

        isInShineStart = (smashbot_state.action == Action.DOWN_B_STUN or \
            smashbot_state.action == Action.DOWN_B_GROUND_START or \
            smashbot_state.action == Action.DOWN_B_GROUND)

        #Jump out of shine
        if isInShineStart and smashbot_state.action_frame >= 3 and smashbot_state.on_ground:
            controller.press_button(Button.BUTTON_Y)
            #controller.tilt_analog(Button.BUTTON_MAIN, int(smashbot_state.facing), .5) #advancing JC shine
            self.interruptible = False
            return

        jcstates = [Action.DOWN_B_GROUND, Action.DASHING, Action.RUNNING]
        if smashbot_state.action in jcstates:
            controller.press_button(Button.BUTTON_Y)
            #controller.tilt_analog(Button.BUTTON_MAIN, int(smashbot_state.facing), .5) #advancing JC shine
            self.interruptible = False
            return

        # Catchall
        self.interruptible = True
        controller.empty_input()
