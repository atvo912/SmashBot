#include <cmath>
#include <math.h>
#include <iostream>

#include "Bait.h"
#include "../Constants.h"
#include "../Tactics/CloseDistance.h"
#include "../Tactics/Wait.h"
#include "../Tactics/Parry.h"
#include "../Tactics/ShineCombo.h"
#include "../Tactics/Laser.h"
#include "../Tactics/Edgeguard.h"
#include "../Tactics/Juggle.h"

Bait::Bait()
{
    m_tactic = NULL;
    m_attackFrame = 0;
    m_lastAction = (ACTION)m_state->m_memory->player_one_action;
    m_shieldedAttack = false;
    m_actionChanged = true;
    m_lastActionCount = 0;
}

Bait::~Bait()
{
    delete m_tactic;
}

void Bait::DetermineTactic()
{
    //std::cout << std::abs(m_state->m_memory->player_one_x - m_state->m_memory->player_two_x) << std::endl;

    //Update the attack frame if the enemy started a new action
    if((m_lastAction != (ACTION)m_state->m_memory->player_one_action) ||
        (m_state->m_memory->player_one_action_counter > m_lastActionCount) ||
        (m_state->m_memory->player_one_action_frame == 1))
    {
        m_lastActionCount = m_state->m_memory->player_one_action_counter;
        m_shieldedAttack = false;
        m_actionChanged = true;
        m_lastAction = (ACTION)m_state->m_memory->player_one_action;
        if(isAttacking((ACTION)m_state->m_memory->player_one_action))
        {
            m_attackFrame = m_state->m_memory->frame;
        }
    }
    //Continuing same previous action
    else
    {
        m_actionChanged = false;
        if(m_state->m_memory->player_one_action == SHIELD_STUN)
        {
            m_shieldedAttack = true;
        }
    }
    if(!isAttacking((ACTION)m_state->m_memory->player_one_action))
    {
        m_attackFrame = 0;
    }

	//If we're not in a state to interupt, just continue with what we've got going
	if((m_tactic != NULL) && (!m_tactic->IsInterruptible()))
	{
		m_tactic->DetermineChain();
		return;
	}

    //If we're still warping in at the start of the match, then just hang out and do nothing
    if(m_state->m_memory->player_two_action == ENTRY ||
        m_state->m_memory->player_two_action == ENTRY_START ||
        m_state->m_memory->player_two_action == ENTRY_END)
    {
        CreateTactic(Wait);
        m_tactic->DetermineChain();
        return;
    }

	//Calculate distance between players
	double distance = pow(std::abs(m_state->m_memory->player_one_x - m_state->m_memory->player_two_x), 2);
	distance += pow(std::abs(m_state->m_memory->player_one_y - m_state->m_memory->player_two_y), 2);
	distance = sqrt(distance);

    //If we're able to shine p1 right now, let's do that
    if(std::abs(distance) < FOX_SHINE_RADIUS)
    {
        //Are we in a state where we can shine?
        if(ReadyForAction(m_state->m_memory->player_two_action))
        {
            //Is the opponent in a state where they can get hit by shine?
            if(m_state->m_memory->player_one_action != SHIELD &&
                m_state->m_memory->player_one_action != SHIELD_REFLECT &&
                m_state->m_memory->player_one_action != MARTH_COUNTER &&
                m_state->m_memory->player_one_action != MARTH_COUNTER_FALLING &&
                m_state->m_memory->player_one_action != EDGE_CATCHING)
            {
                CreateTactic(ShineCombo);
                m_tactic->DetermineChain();
                return;
            }
        }
    }

    //If we need to defend against an attack, that's next priority. Unless we've already shielded this attack
    if(!m_shieldedAttack && distance < MARTH_FSMASH_RANGE)
    {
        //Don't bother parrying if the attack is in the wrong direction
        bool player_one_is_to_the_left = (m_state->m_memory->player_one_x - m_state->m_memory->player_two_x > 0);
        if(m_state->m_memory->player_one_facing != player_one_is_to_the_left || (isReverseHit((ACTION)m_state->m_memory->player_one_action)))
        {
            if(isAttacking((ACTION)m_state->m_memory->player_one_action))
            {
                //If the p1 action changed, scrap the old Parry and make a new one.
                if(m_actionChanged)
                {
                    delete m_tactic;
                    m_tactic = NULL;
                }

                CreateTactic2(Parry, m_attackFrame);
                m_tactic->DetermineChain();
                return;
            }
        }
    }

	//If we're far away, just laser
	if(std::abs(m_state->m_memory->player_one_x - m_state->m_memory->player_two_x) > 90)
	{
        CreateTactic(Laser);
        m_tactic->DetermineChain();
        return;
    }

    //If the opponent is off the stage, let's edgeguard them
    //NOTE: Sometimes players can get a little below 0 in Y coordinates without being off the stage
    if(std::abs(m_state->m_memory->player_one_x) > m_state->getStageEdgePosition() || m_state->m_memory->player_one_y < -5.5)
    {
        CreateTactic(Edgeguard);
        m_tactic->DetermineChain();
        return;
    }

    //If we're not in shine range, get in close
    if(std::abs(m_state->m_memory->player_one_x - m_state->m_memory->player_two_x) > FOX_SHINE_RADIUS)
    {
        CreateTactic(CloseDistance);
        m_tactic->DetermineChain();
        return;
    }
    //If we're in close and p2 is sheilding, just wait
    if(m_state->m_memory->player_one_action == ACTION::SHIELD)
    {
        CreateTactic(Wait);
        m_tactic->DetermineChain();
        return;
    }
    //TODO: For now, just default to waiting if nothing else fits
    CreateTactic(Wait);
    m_tactic->DetermineChain();
    return;
}

bool Bait::isAttacking(ACTION action)
{
    switch(action)
    {
        case FSMASH_MID:
        case DOWNSMASH:
        case UPSMASH:
        case DASH_ATTACK:
        case GRAB:
        case GRAB_RUNNING:
        case FTILT_HIGH:
        case FTILT_HIGH_MID:
        case FTILT_MID:
        case FTILT_LOW_MID:
        case FTILT_LOW:
        case UPTILT:
        case DOWNTILT:
        case SWORD_DANCE_1:
        case SWORD_DANCE_2_HIGH:
        case SWORD_DANCE_2_MID:
        case SWORD_DANCE_3_HIGH:
        case SWORD_DANCE_3_MID:
        case SWORD_DANCE_3_LOW:
        case SWORD_DANCE_4_HIGH:
        case SWORD_DANCE_4_MID:
        case SWORD_DANCE_4_LOW:
        case SWORD_DANCE_1_AIR:
        case SWORD_DANCE_2_HIGH_AIR:
        case SWORD_DANCE_2_MID_AIR:
        case SWORD_DANCE_3_HIGH_AIR:
        case SWORD_DANCE_3_MID_AIR:
        case SWORD_DANCE_3_LOW_AIR:
        case SWORD_DANCE_4_HIGH_AIR:
        case SWORD_DANCE_4_MID_AIR:
        case SWORD_DANCE_4_LOW_AIR:
        case UP_B:
        case UP_B_GROUND:
        case NAIR:
        case UAIR:
        case DAIR:
        case BAIR:
        case FAIR:
        case NEUTRAL_ATTACK_1:
        case NEUTRAL_ATTACK_2:
        case NEUTRAL_ATTACK_3:
        case NEUTRAL_B_ATTACKING:
        case NEUTRAL_B_ATTACKING_AIR:
        {
            return true;
        }
        default:
        {
            return false;
        }
    }
}

bool Bait::isReverseHit(ACTION action)
{
    switch(action)
    {
        case DOWNSMASH:
        case UPSMASH:
        case GRAB_RUNNING:
        case UPTILT:
        case NAIR:
        case UAIR:
        case DAIR:
        case BAIR:
        {
            return true;
        }
        default:
        {
            return false;
        }
    }
}
