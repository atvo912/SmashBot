import melee
import Chains
import math
from melee.enums import Action, Button, Character
from Tactics.tactic import Tactic
from Chains.smashattack import SMASH_DIRECTION
from Chains.shffl import SHFFL_DIRECTION
from Chains.grabandthrow import THROW_DIRECTION
from Chains.tiltattack import TILT_DIRECTION

class Punish(Tactic):
    # How many frames do we have to work with for the punish
    def framesleft(opponent_state, framedata):
        # For some dumb reason, the game shows the standing animation as having a large hitstun
        #   manually account for this
        if opponent_state.action == Action.STANDING:
            return 1

        # Don't try to punish Samus knee_bend, because they will go into UP_B and it has invulnerability
        if opponent_state.action == Action.KNEE_BEND and opponent_state.character == Character.SAMUS:
            return 0

        # Samus UP_B invulnerability
        if opponent_state.action in [Action.SWORD_DANCE_3_MID, Action.SWORD_DANCE_3_LOW] and \
                opponent_state.character == Character.SAMUS and opponent_state.action_frame <= 5:
            return 0

        # Samus morph ball
        if opponent_state.character == Character.SAMUS and opponent_state.action in [Action.SWORD_DANCE_4_MID, Action.SWORD_DANCE_4_HIGH, Action.NEUTRAL_B_CHARGING]:
            return 1

        # Pikachu skull bash, thunder
        if opponent_state.action in [Action.NEUTRAL_B_FULL_CHARGE, Action.NEUTRAL_B_ATTACKING, Action.SWORD_DANCE_2_MID_AIR, Action.SWORD_DANCE_2_HIGH_AIR] and \
                opponent_state.character == Character.PIKACHU:
            return 1

        # Jigglypuff jumps
        if opponent_state.character == Character.JIGGLYPUFF and opponent_state.action in \
                [Action.LASER_GUN_PULL, Action.NEUTRAL_B_CHARGING, Action.NEUTRAL_B_ATTACKING, Action.NEUTRAL_B_FULL_CHARGE, Action.WAIT_ITEM]:
            return 1

        if opponent_state.character == Character.SHEIK:
            if opponent_state.action in [Action.SWORD_DANCE_4_HIGH, Action.SWORD_DANCE_1_AIR]:
                return 17 - opponent_state.action_frame
            if opponent_state.action in [Action.SWORD_DANCE_4_LOW, Action.SWORD_DANCE_2_HIGH_AIR] and opponent_state.action_frame <= 21:
                return 0

        # Shine wait
        if opponent_state.character in [Character.FOX, Character.FALCO]:
            if opponent_state.action in [Action.SWORD_DANCE_2_MID_AIR, Action.SWORD_DANCE_3_HIGH_AIR, Action.SWORD_DANCE_3_LOW_AIR]:
                return 3

        if opponent_state.action == Action.LOOPING_ATTACK_MIDDLE:
            return 1

        if opponent_state.character == Character.SHEIK and opponent_state.action == Action.SWORD_DANCE_2_HIGH:
            return 1

        # Is opponent attacking?
        if framedata.is_attack(opponent_state.character, opponent_state.action):
            # What state of the attack is the opponent in?
            # Windup / Attacking / Cooldown
            attackstate = framedata.attack_state(opponent_state)
            if attackstate == melee.enums.AttackState.WINDUP:
                # Don't try to punish opponent in windup when they're invulnerable
                if opponent_state.invulnerability_left > 0:
                    return 0
                # Don't try to punish standup attack windup
                if opponent_state.action in [Action.GROUND_ATTACK_UP, Action.GETUP_ATTACK]:
                    return 0
                frame = framedata.first_hitbox_frame(opponent_state.character, opponent_state.action)
                return max(0, frame - opponent_state.action_frame - 1)
            if attackstate == melee.enums.AttackState.ATTACKING:
                return 0
            if attackstate == melee.enums.AttackState.COOLDOWN:
                frame = framedata.iasa(opponent_state.character, opponent_state.action)
                return max(0, frame - opponent_state.action_frame)
        if framedata.is_roll(opponent_state.character, opponent_state.action):
            frame = framedata.last_roll_frame(opponent_state.character, opponent_state.action)
            return max(0, frame - opponent_state.action_frame)

        # Opponent is in hitstun
        if opponent_state.hitstun_frames_left > 0:
            # Special case here for lying on the ground.
            #   For some reason, the hitstun count is totally wrong for these actions
            if opponent_state.action in [Action.LYING_GROUND_UP, Action.LYING_GROUND_DOWN]:
                return 1

            # If opponent is in the air, we need to cap the return at when they will hit the ground
            if opponent_state.y > .02 or not opponent_state.on_ground:
                # When will they land?
                speed = opponent_state.speed_y_attack + opponent_state.speed_y_self
                height = opponent_state.y
                gravity = framedata.characterdata[opponent_state.character]["Gravity"]
                termvelocity = framedata.characterdata[opponent_state.character]["TerminalVelocity"]
                count = 0
                while height > 0:
                    height += speed
                    speed -= gravity
                    speed = max(speed, -termvelocity)
                    count += 1
                    # Shortcut if we get too far
                    if count > 120:
                        break
                #return count #need to modify this old line so it returns the lower value between count (projected airtime) and hitstun_frames_left rather than just count.
                return min(count, opponent_state.hitstun_frames_left) #proposed fix

            return opponent_state.hitstun_frames_left

        # Opponent is in a lag state
        if opponent_state.action in [Action.UAIR_LANDING, Action.FAIR_LANDING, \
                Action.DAIR_LANDING, Action.BAIR_LANDING, Action.NAIR_LANDING]:
            # TODO: DO an actual lookup to see how many frames this is
            return 9 - (opponent_state.action_frame // 3)

        # Exception for Jigglypuff rollout
        #   The action frames are weird for this action, and Jiggs is actionable during it in 1 frame
        if opponent_state.character == Character.JIGGLYPUFF and \
                opponent_state.action in [Action.SWORD_DANCE_1, Action.NEUTRAL_B_FULL_CHARGE_AIR, Action.SWORD_DANCE_4_LOW, \
                Action.SWORD_DANCE_4_MID, Action.SWORD_DANCE_3_LOW]:
            return 1

        # Opponent is in a B move
        if framedata.is_bmove(opponent_state.character, opponent_state.action):
            return framedata.frame_count(opponent_state.character, opponent_state.action) - opponent_state.action_frame

        return 1

    # Static function that returns whether we have enough time to run in and punish,
    # given the current gamestate. Either a shine or upsmash
    def canpunish(smashbot_state, opponent_state, gamestate, framedata):
        # Can't punish opponent in shield
        shieldactions = [Action.SHIELD_START, Action.SHIELD, Action.SHIELD_RELEASE, \
            Action.SHIELD_STUN, Action.SHIELD_REFLECT]
        if opponent_state.action in shieldactions:
            return False

        if smashbot_state.off_stage:
            return False

        firefox = opponent_state.action == Action.SWORD_DANCE_3_LOW and opponent_state.character in [Character.FOX, Character.FALCO]
        if firefox and opponent_state.y > 15:
            return False

        left = Punish.framesleft(opponent_state, framedata)
        # Will our opponent be invulnerable for the entire punishable window?
        if left <= opponent_state.invulnerability_left:
            return False

        if left < 1:
            return False

        if framedata.is_roll(opponent_state.character, opponent_state.action):
            return True

        # Can we shine right now without any movement?
        shineablestates = [Action.TURNING, Action.STANDING, Action.WALK_SLOW, Action.WALK_MIDDLE, \
            Action.WALK_FAST, Action.EDGE_TEETERING_START, Action.EDGE_TEETERING, Action.CROUCHING, \
            Action.RUNNING]

        #TODO: Wrap the shine range into a helper
        foxshinerange = 10 #lowered from 11.8
        inshinerange = gamestate.distance < foxshinerange

        if inshinerange and smashbot_state.action in shineablestates:
            return True

        #TODO: Wrap this up into a helper
        foxrunspeed = 2.2
        #TODO: Subtract from this time spent turning or transitioning
        # Assume that we can run at max speed toward our opponent
        # We can only run for framesleft-1 frames, since we have to spend at least one attacking
        potentialrundistance = (left-1) * foxrunspeed

        if gamestate.distance - potentialrundistance < foxshinerange:
            return True
        return False

    def step(self, gamestate, smashbot_state, opponent_state):
        self._propagate  = (gamestate, smashbot_state, opponent_state)

        #If we can't interrupt the chain, just continue it
        if self.chain != None and not self.chain.interruptible:
            self.chain.step(gamestate, smashbot_state, opponent_state)
            return

        # TODO: This should be all inactionable animations, actually
        inactionablestates = [Action.THROW_DOWN, Action.THROW_UP, Action.THROW_FORWARD, Action.THROW_BACK, Action.UAIR_LANDING, Action.FAIR_LANDING, \
                Action.DAIR_LANDING, Action.BAIR_LANDING, Action.NAIR_LANDING, Action.UPTILT, Action.DOWNTILT, Action.UPSMASH, \
                Action.DOWNSMASH]
        if smashbot_state.action in inactionablestates:
            self.pickchain(Chains.Nothing)
            return

        # Can we charge an upsmash right now?
        framesleft = Punish.framesleft(opponent_state, self.framedata)
        if self.logger:
            self.logger.log("Notes", "framesleft: " + str(framesleft) + " ", concat=True)

        # How many frames do we need for an upsmash?
        # It's 7 frames normally, plus some transition frames
        # 1 if in shield, shine, or dash/running
        framesneeded = 7 # Maybe add some logic here to LOOK at framesleft, and then choose a specific option depending on how large it is? Or maybe just leave as-is.
        shieldactions = [Action.SHIELD_START, Action.SHIELD, Action.SHIELD_RELEASE, \
            Action.SHIELD_STUN, Action.SHIELD_REFLECT]
        shineactions = [Action.DOWN_B_STUN, Action.DOWN_B_GROUND_START, Action.DOWN_B_GROUND]
        runningactions = [Action.DASHING, Action.RUNNING]
        if smashbot_state.action in shieldactions:
            framesneeded += 1 #lowered from 3 to 1
        if smashbot_state.action in shineactions:
            framesneeded += 1 #lowered from 3 to 1
        if smashbot_state.action in runningactions:
            framesneeded += 1 #lowered from 3 to 1

        endposition = opponent_state.x
        isroll = self.framedata.is_roll(opponent_state.character, opponent_state.action)
        slideoff = False

        # If we have the time....
        if framesneeded <= framesleft:
            # Calculate where the opponent will end up
            if opponent_state.hitstun_frames_left > 0:
                endposition = opponent_state.x + self.framedata.slide_distance(opponent_state, opponent_state.speed_x_attack, framesleft)

            if isroll:
                endposition = self.framedata.roll_end_position(opponent_state, gamestate.stage)

                initialrollmovement = 0
                facingchanged = False
                try:
                    initialrollmovement = self.framedata.framedata[opponent_state.character][opponent_state.action][opponent_state.action_frame]["locomotion_x"]
                    facingchanged = self.framedata.framedata[opponent_state.character][opponent_state.action][opponent_state.action_frame]["facing_changed"]
                except KeyError:
                    pass
                backroll = opponent_state.action in [Action.ROLL_BACKWARD, Action.GROUND_ROLL_BACKWARD_UP, \
                    Action.GROUND_ROLL_BACKWARD_DOWN, Action.BACKWARD_TECH]
                if not (opponent_state.facing ^ facingchanged ^ backroll):
                    initialrollmovement = -initialrollmovement

                speed = opponent_state.speed_x_attack + opponent_state.speed_ground_x_self - initialrollmovement
                endposition += self.framedata.slide_distance(opponent_state, speed, framesleft)

                # But don't go off the end of the stage
                if opponent_state.action in [Action.TECH_MISS_DOWN, Action.TECH_MISS_UP, Action.NEUTRAL_TECH]:
                    if abs(endposition) > melee.stages.EDGE_GROUND_POSITION[gamestate.stage]:
                        slideoff = True
                endposition = max(endposition, -melee.stages.EDGE_GROUND_POSITION[gamestate.stage])
                endposition = min(endposition, melee.stages.EDGE_GROUND_POSITION[gamestate.stage])


            # And we're in range...
            # Take our sliding into account
            slidedistance = self.framedata.slide_distance(smashbot_state, smashbot_state.speed_ground_x_self, framesleft)
            smashbot_endposition = slidedistance + smashbot_state.x

            # Do we have to consider character pushing?
            # Are we between the character's current and predicted position?
            if opponent_state.x < smashbot_endposition < endposition or \
                    opponent_state.x > smashbot_endposition > endposition:
                # Add a little bit of push distance along that path
                # 0.3 pushing for max of 16 frames
                #TODO Needs work here
                onleft = smashbot_state.x < opponent_state.x
                if onleft:
                    smashbot_endposition -= 4.8
                else:
                    smashbot_endposition += 4.8

            facing = smashbot_state.facing == (smashbot_endposition < endposition)
            # Remember that if we're turning, the attack will come out the opposite way
            # On f1 of smashturn, smashbot hasn't changed directions yet. On/after frame 2, it has. Tilt turn may be a problem.
            if smashbot_state.action == Action.TURNING and smashbot_state.action_frame == 1:
                facing = not facing

            # Get height of opponent at the targeted frame
            height = opponent_state.y
            firefox = opponent_state.action == Action.SWORD_DANCE_3_LOW and opponent_state.character in [Character.FOX, Character.FALCO]
            speed = opponent_state.speed_y_attack
            gravity = self.framedata.characterdata[opponent_state.character]["Gravity"]
            termvelocity = self.framedata.characterdata[opponent_state.character]["TerminalVelocity"]
            #if not opponent_state.on_ground and not firefox:
                # Loop through each frame and count the distances
                #for i in range(framesleft):
                    #speed -= gravity
                    # We can't go faster than termvelocity downwards
                    #speed = max(speed, -termvelocity)
                    #height += speed

            if self.logger:
                self.logger.log("Notes", "endposition: " + str(endposition) + " ", concat=True)
                self.logger.log("Notes", "smashbot_endposition: " + str(smashbot_endposition) + " ", concat=True)
                self.logger.log("Notes", "height" + str(height) + " ", concat=True)
                self.logger.log("Notes", "Distance: " + str(gamestate.distance), concat=True)

            distance = abs(endposition - smashbot_endposition)

            if not slideoff and distance < 14.5 and -5 < height < 17: #REMOVED -5 < height < 8 to make Smashbot attempt chaingrabbing #Consider adding some conditions here/below to check for CC/ASDI percentages and/or other relevant percentages
                #if smashbot_state.action == Action.SHIELD_RELEASE and smashbot_state.action_frame == 1:
                    #self.pickchain(Chains.Powershield)
                if facing:
                    # Do the upsmash
                    # NOTE: If we get here, we want to delete the chain and start over
                    #   Since the amount we need to charge may have changed
                    # Tai would like to add some more complexity here where we have a larger variety of chains to select from, with varying stored framesneeded values & some logic with a random function for choosing one.
                    self.chain = None
                    if (opponent_state.action in [Action.TECH_MISS_DOWN, Action.TECH_MISS_UP]) or (opponent_state.percent >= 100):
                        self.pickchain(Chains.SmashAttack, [framesleft-framesneeded-1, SMASH_DIRECTION.UP])
                    ##EVERYTHING BELOW HERE IS EXPERIMENTAL
                    #if framesleft < 20 and framesleft > 9:
                        #self.pickchain(Chains.Nothing)
                        return
                    if (framesleft in range(7,9) and opponent_state.action not in [Action.TECH_MISS_DOWN, Action.TECH_MISS_UP]) or (smashbot_state.action == Action.GRAB_WAIT):
                        if opponent_state.character in [Character.CPTFALCON, Character.FALCO, Character.FOX]:
                            self.pickchain(Chains.GrabAndThrow, [THROW_DIRECTION.UP]) #test dthrow instead of usmash
                        else:
                            self.pickchain(Chains.GrabAndThrow, [THROW_DIRECTION.DOWN])
                        #self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.UP]) #test shffl uair instead of usmash
                        #self.pickchain(Chains.TiltAttack, [TILT_DIRECTION.TURNAROUND]) #test utilt instead of usmash
                    #if framesleft == 9 or framesleft == 8 or framesleft == 7 and distance < 0.5 and (smashbot_state.action != Action.GRAB_WAIT):
                        #self.pickchain(Chains.TiltAttack, [TILT_DIRECTION.UP])
                    ##EVERTHING ABOVE HERE IS EXPERIMENTAL
                        return
                else:  #add functionality to look for utilt here, requires creating tiltattack.py chain
                    # Do the bair if there's not enough time to wavedash, but we're facing away and out of shine range
                    #   This shouldn't happen often, but can if we're pushed away after powershield
                    offedge = melee.stages.edgegroundposition(gamestate.stage) < abs(endposition)
                    if (framesleft in range(7,9)) and not offedge: #removed framesleft condition and distance > 9 condition for SHFFL bair
                        #self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.BACK])
                        self.pickchain(Chains.TiltAttack, [TILT_DIRECTION.UP]) #test utilt instead of usmash
                        return
            # If we're not in attack range, and can't run, then maybe we can wavedash in
            #   Now we need more time for the wavedash. 10 frames of lag, and 3 jumping
            framesneeded = 13
            if framesneeded <= framesleft:
                if smashbot_state.action in shieldactions or smashbot_state.action in shineactions:
                    self.pickchain(Chains.Wavedash)
                    return

        # We can't smash our opponent, so let's just shine instead. Do we have time for that?
        #TODO: Wrap the shine range into a helper
        framesneeded = 1
        if smashbot_state.action == Action.DASHING:
            framesneeded = 2
        if smashbot_state.action in [Action.SHIELD_RELEASE, Action.SHIELD]:
            framesneeded = 4
        if smashbot_state.action in [Action.DOWN_B_STUN, Action.DOWN_B_GROUND_START, Action.DOWN_B_GROUND]:
            framesneeded = 4

        foxshinerange = 10 # Lowered from 11.8
        if smashbot_state.action == Action.DASHING:
            foxshinerange = 9

        if gamestate.distance < foxshinerange:
            if framesneeded <= framesleft:
            #if framesleft in range(1,5): #attempted changed to prevent triggering waveshines when we would prefer to wait for other punishes
                # Also, don't shine someone in the middle of a roll
                if (not isroll) or (opponent_state.action_frame < 3):
                    self.chain = None
                    # If we are facing towards the edge, don't wavedash off of it
                    #   Reduce the wavedash length
                    x = 1
                    # If we are really close to the edge, wavedash straight down
                    if melee.stages.EDGE_GROUND_POSITION[gamestate.stage] - abs(smashbot_state.x) < 3:
                        x = 0
                    self.pickchain(Chains.Waveshine, [x])
                    return
            # We're in range, but don't have enough time. Let's try turning around to do a pivot.
            else:
                self.chain = None
                # Pick a point right behind us
                pivotpoint = smashbot_state.x
                dashbuffer = 5
                if smashbot_state.facing:
                    dashbuffer = -dashbuffer
                pivotpoint += dashbuffer
                self.pickchain(Chains.DashDance, [pivotpoint])
                return

        # Kill the existing chain and start a new one
        self.chain = None
        self.pickchain(Chains.DashDance, [endposition])
