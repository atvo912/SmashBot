import melee
import Chains
from melee.enums import Action
from Tactics.tactic import Tactic
from Chains.smashattack import SMASH_DIRECTION
from Tactics.punish import Punish
from melee.enums import Character

class Infinite(Tactic):
    def __init__(self, logger, controller, framedata, difficulty):
        Tactic.__init__(self, logger, controller, framedata, difficulty)

    def killpercent(opponent_state):
        character = opponent_state.character
        if character == Character.CPTFALCON:
            return 113
        if character == Character.FALCO:
            return 103
        if character == Character.FOX:
            return 96
        if character == Character.SHEIK:
            return 92
        if character == Character.PIKACHU:
            return 73
        if character == Character.PEACH:
            return 80
        if character == Character.ZELDA:
            return 70
        if character == Character.MARTH:
            return 89
        if character == Character.JIGGLYPUFF:
            return 55
        if character == Character.SAMUS:
            return 89
        return 100

    def caninfinite(smashbot_state, opponent_state, gamestate, framedata, difficulty):
        isroll = framedata.is_roll(opponent_state.character, opponent_state.action)

        if opponent_state.action in [Action.SHIELD_START, Action.SHIELD, \
                Action.SHIELD_STUN, Action.SHIELD_REFLECT]:
            return False

        # Don't try to infinite if we're on a platform
        if smashbot_state.y > 2:
            return False

        # Should we try a waveshine infinite?
        #   They need to have high friction and not fall down
        if opponent_state.action in [Action.STANDING, Action.TURNING, Action.DASHING, Action.RUNNING, \
                Action.WALK_SLOW, Action.WALK_MIDDLE, Action.WALK_FAST]:
            return False

        framesleft = Punish.framesleft(opponent_state, framedata, smashbot_state)
        # This is off by one for hitstun
        framesleft -= 1

        # Give up the infinite if we're in our last dashing frame, and are getting close to the edge
        #  We are at risk of running off the edge when this happens
        if (smashbot_state.action == Action.DASHING and smashbot_state.action_frame >= 11):
            if (smashbot_state.speed_ground_x_self > 0) == (smashbot_state.x > 0):
                edge_x = melee.stages.EDGE_GROUND_POSITION[gamestate.stage]
                if opponent_state.x < 0:
                    edge_x = -edge_x
                edgedistance = abs(edge_x - smashbot_state.x)
                if edgedistance < 16: #increased from 16 due to Smashbot still wavedashing offstage even when he waveshines at an edgedistance of 25
                    return False

        # If opponent is attacking, don't infinite
        if framedata.is_attack(opponent_state.character, opponent_state.action):
            return False

        # If opponent is going to slide to the edge, then we have to stop
        endposition = opponent_state.x + framedata.slide_distance(opponent_state, opponent_state.speed_x_attack, framesleft)
        if abs(endposition)+5 > melee.stages.EDGE_GROUND_POSITION[gamestate.stage]:
            return False

        if framedata.characterdata[opponent_state.character]["Friction"] >= 0.06 and \
                opponent_state.hitstun_frames_left > 1 and not isroll and opponent_state.on_ground \
                and opponent_state.percent < Infinite.killpercent(opponent_state):
            return True

        return False

    def step(self, gamestate, smashbot_state, opponent_state):
        self._propagate  = (gamestate, smashbot_state, opponent_state)

        #If we can't interrupt the chain, just continue it
        if self.chain != None and not self.chain.interruptible:
            self.chain.step(gamestate, smashbot_state, opponent_state)
            return

        framesleft = Punish.framesleft(opponent_state, self.framedata, smashbot_state)
        # This is off by one for hitstun
        framesleft -= 1

        shinerange = 9.9
        if smashbot_state.action == Action.RUNNING:
            shinerange = 12.8
        if smashbot_state.action == Action.DASHING:
            shinerange = 9.5

        # If we shine too close to the edge while accelerating horizontally, we can slide offstage and get into trouble
        distance_from_edge = melee.stages.EDGE_GROUND_POSITION[gamestate.stage] - abs(smashbot_state.x)
        edgetooclose = smashbot_state.action == Action.EDGE_TEETERING_START or distance_from_edge < 5

        # Try to do the shine
        if gamestate.distance < shinerange and not edgetooclose:
            # Emergency backup shine. If we don't shine now, they'll get out of the combo
            if framesleft == 1:
                self.chain = None
                self.pickchain(Chains.Waveshine)
                return

            # Cut the run short and just shine now. Don't wait for the cross-up
            #   This is here to prevent running too close to the edge and sliding off
            if smashbot_state.action in [Action.RUNNING, Action.RUN_BRAKE, Action.CROUCH_START] and distance_from_edge < 16:
                self.chain = None
                self.pickchain(Chains.Waveshine)
                return

            # We always want to try to shine our opponent towards the center of the stage
            # If we are lined up right now, do the shine
            if (smashbot_state.x < opponent_state.x < 0) or (0 < opponent_state.x < smashbot_state.x):
                self.chain = None
                self.pickchain(Chains.Waveshine)
                return

            # There can be an issue with shining "towards" center if smashbot/opponent are on opposite sides of x = 0
            if abs(smashbot_state.x) < 10 and abs(opponent_state.x) < 10:
                self.chain = None
                self.pickchain(Chains.Waveshine)
                return

            # If we are running away from our opponent, just shine now
            onright = opponent_state.x < smashbot_state.x
            if (smashbot_state.speed_ground_x_self > 0) == onright:
                self.chain = None
                self.pickchain(Chains.Waveshine)
                return

        if smashbot_state.action == Action.LANDING_SPECIAL and smashbot_state.action_frame < 28:
            self.pickchain(Chains.Nothing)
            return

        if not (smashbot_state.action == Action.DOWN_B_GROUND_START and smashbot_state.action_frame in [1,2]):
            self.pickchain(Chains.Run, [opponent_state.x > smashbot_state.x])
            return
        return
