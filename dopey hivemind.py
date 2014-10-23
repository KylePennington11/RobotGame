# Learned syntax from Simplebot by ramk13

import rg, random, operator
from time import time
from math import sqrt,sin,cos,pi,ceil

turn_number = -1
attack_damage = 10
debug_enabled = False

spawn = set(rg.settings.spawn_coords)
obstacle = set(rg.settings.obstacles)
center = rg.CENTER_POINT

#====================================
#============  FUNCTIONS  ===========
#====================================  

def debug(text):
    if debug_enabled:
        print text

def around((x,y),radius=1):
    points = set()
    for i in xrange(radius+1):
        points.add((-i+x,-radius+i+y))
        points.add((-i+x,radius-i+y))
        points.add((i+x,-radius+i+y))
        points.add((i+x,radius-i+y))
    return points - obstacle

def diag_around((x,y)):
    offsets = ((1, 1), (1, -1), (-1, 1), (-1, -1))
    return set([(x + dx, y + dy) for dx, dy in offsets])-obstacle

def circle(radius, n):
    circle_coords = set()
    for i in range(n):
        theta = i*2*pi/float(n)
        x = int(radius*sin(theta)) + 9
        y = int(radius*cos(theta)) + 9
        coord = (x,y)
        circle_coords.add(coord)
    return circle_coords

# Function to find the closest bot to a specific location by diagonal distance
# Also used to pick the direction closest to the movement goal
def mindist (bots, loc):
    return min(bots,key=lambda x:rg.dist(x, loc))
    
class Robot:

    debug('Initiated!!!')

    def act(self, game):
        t0 = time()

              # If moving save the location we are moving to 
        def moving(me, loc, guaranteed=True):
            taken_moves.add(loc)
            if guaranteed:
                freed_moves.add(me)
            return ['move', loc]

        # If staying save the location that we are at
        def staying(act,loc=center):
            return [act, loc]
            
        # Function to find bot with the least health
        def minhp (bots):
            return min(bots,key=lambda x:robots[x].hp)


        #====================================
        #============  PRIORITY  ============
        #====================================            
        def determine_priority(loc):
            me = loc
            adjacent = around(me)
            adjacent_enemy = adjacent & enemy
            near_enemy = around(me,2) & enemy
            adjacent_team = adjacent & team

            in_spawn = spawn & set([me])

            points_spawn = 10*len(in_spawn)*(11-turns_till_spawn)
            points_enemies = 15*len(adjacent_enemy)
            points_enemies = points_enemies + 5*len(near_enemy)
            points_team = 5*len(adjacent_team)
            points_hp = (500-robots[me].hp*10)/10

            priority = points_spawn + points_enemies + points_team + points_hp

            debug(str(me) + ': ' + str(priority) + ' || ' + str(points_spawn) + ' - ' + str(points_enemies) + ' - ' + str(points_team) + ' - ' + str(points_hp))

            return priority


        #====================================
        #==========  PICK TARGET  ===========
        #====================================
        def score_enemy(loc):
            # the bigger the more screwed they are...
            adjacent = around(loc)
            enemy_not_me = enemy - set([loc])

            adjacent_team = adjacent & team
            adjacent_team2 = set(filter(lambda k:around(k) & team, adjacent))

            adjacent_enemy = adjacent & enemy_not_me

            safemove           = adjacent-adjacent_team-adjacent_team2-spawn-enemy
            semisafemove       = adjacent & adjacent_team2
            spawnmoves = (adjacent & spawn)-adjacent_team-enemy

            hp_score = robots[loc].hp*2

            score = len(adjacent_enemy)*20 + len(safemove)*50 +  len(semisafemove)*10 + len(spawnmoves)*5 + hp_score

            return 300-score


        #====================================
        #========  DETERMINE MOVE  ==========
        #====================================
        def determine_move(loc):

 
            #====================================
            #=============  SETS  ===============
            #====================================

            me = loc
            team_not_me = team - set([me])

            adjacent = around(me)

            adjacent_enemy = adjacent & enemy
            adjacent_enemy2 = set(filter(lambda k:around(k) & enemy, adjacent))

            adjacent_team = adjacent & team_not_me
            adjacent_team_blocking = adjacent_team - spawn - had_turn

            safemove           = adjacent-adjacent_enemy-adjacent_enemy2-spawn-(team-freed_moves)-taken_moves
            semisafemove       = adjacent-adjacent_enemy                -spawn-(team-freed_moves)-taken_moves
            safemove_withspawn = adjacent-adjacent_enemy-adjacent_enemy2      -(team-freed_moves)-taken_moves
            semisafemove_spawn = adjacent-adjacent_enemy                      -(team-freed_moves)-taken_moves

            if enemy:
                closest_enemy = mindist(enemy,me)
            else:
                closest_enemy = center

            if fighting:
                closest_fighting = mindist(fighting,me)
            else:
                closest_fighting = closest_enemy

            if team_not_me:
                closest_team = mindist(team_not_me,me)
            else:
                closest_team = center

            if coords:
                closest_coord = mindist(coords,me)
                coords.remove(closest_coord)
            else:
                closest_coord = center

            if turns_till_spawn == 0:
                for s in spawn:
                    taken_moves.add(s)

            #====================================
            #=========== LOGIC ==================
            #====================================


            if me in spawn and closest_enemy not in fighting:

                if safemove:
                    move = moving(me,mindist(safemove,closest_enemy),True)
                    debug(str(me) + ': Moving safely to enemy ' + str(closest_enemy))

                # elif len(safemove_withspawn)>0 and turn_number%10<5 and turn_number%10>0:
                #     move = moving(mindist(safemove_withspawn,closest_enemy),True)
                #     debug(str(me) + ': Moving on spawn to enemy ' + str(closest_enemy))

                elif semisafemove:
                    move = moving(me,mindist(semisafemove,team_center))
                    debug(str(me) + ': Moving semi-safely to center ' + str(team_center))

                elif turns_till_spawn == 0:
                    move = staying('suicide')
                    debug(str(me) + ':Im dead anyway...')

                elif adjacent_team_blocking:
                    move = moving(me,mindist(adjacent_team_blocking,team_center))
                    debug(str(me) + ': Move bitch, get out the way! ' + str(adjacent_team_blocking))

                elif semisafemove_spawn:
                    move = moving(me,mindist(semisafemove_spawn,team_center))
                    debug(str(me) + ': Moving semi-safely on spawn to center ' + str(team_center))

                elif adjacent_enemy:
                    target = minhp(adjacent_enemy)
                    move = staying('attack',target)
                    fighting.add(target) 
                    debug(str(me) + ': Stuck in spawn. I might as well fight while I''m here!' + str(target))    

                else:
                    move = staying('guard')
                    debug(str(me) + ': guarding in spawn')

            elif adjacent_enemy:
                potential_damage = attack_damage*len(adjacent_enemy)
                
                if potential_damage>=robots[me].hp and (potential_damage/2)<robots[me].hp:

                    if safemove:
                        move = moving(me,mindist(safemove,team_center),True)
                        debug(str(me) + ': Moving safely to center ' + str(team_center))

                    elif adjacent_team_blocking:
                        move = moving(me,mindist(adjacent_team_blocking,team_center))
                        debug(str(me) + ': Move bitch, get out the way! I''m getting low!' + str(adjacent_team_blocking))

                    elif safemove_withspawn and turns_till_spawn != 0:
                        move = moving(me,mindist(safemove_withspawn,team_center),True)
                        debug(str(me) + ': Moving on spawn to center ' + str(team_center))

                    else:
                        move = staying('guard')
                        debug(str(me) + ': Baiting... ')

                elif potential_damage>=robots[me].hp:

                    if safemove:
                        move = moving(me,mindist(safemove,team_center),True)
                        debug(str(me) + ': Moving safely to center ' + str(team_center))

                    elif adjacent_team_blocking:
                        move = moving(me,mindist(adjacent_team_blocking,team_center))
                        debug(str(me) + ': Move bitch, get out the way! I''m about to die!' + str(adjacent_team_blocking))

                    elif safemove_withspawn and turns_till_spawn != 0:
                        move = moving(me,mindist(safemove_withspawn,team_center),True)
                        debug(str(me) + ': Moving on spawn in last ditch effort to survive! ' + str(team_center))

                    else:
                        move = staying('suicide')
                        debug(str(me) + ': Goodbye cruel world...')

                # >1 adjacent enemys
                elif len(adjacent_enemy)>1:
                    potential_damage = attack_damage*len(adjacent_enemy)

                    if potential_damage < robots[me].hp and robots[minhp(adjacent_enemy)].hp <= 5:
                        target = minhp(adjacent_enemy)
                        move = staying('attack',target)
                        fighting.add(target) 
                        debug(str(me) + ': Attacking lowest enemy; I think I can take him. Hopefully he doesn''t run... ' + str(target))    

                    elif safemove:
                        move = moving(me,mindist(safemove,team_center),True)
                        debug(str(me) + ': Moving safely to center ' + str(team_center))

                    elif semisafemove:
                        move = moving(me,mindist(semisafemove,team_center))
                        debug(str(me) + ': Moving semi-safely to center ' + str(team_center))

                    elif semisafemove_spawn:
                        move = moving(me,mindist(semisafemove_spawn,team_center))
                        debug(str(me) + ': Trying spawn to escape to center ' + str(team_center)) 

                    else:   # we have to fight
                        target = minhp(adjacent_enemy)
                        move = staying('attack',target)
                        fighting.add(target)
                        debug(str(me) + ': HELP!!! I''M TRAPPED!!! Attacking lowest enemy ' + str(target))

                # 1 adjacent enemy
                elif robots[minhp(adjacent_enemy)].hp <= 5 and robots[me].hp > attack_damage*2 and minhp(adjacent_enemy) not in chasing and not (turns_till_spawn == 0 and minhp(adjacent_enemy) in spawn):
                    move = moving(me,minhp(adjacent_enemy))
                    chasing.add(minhp(adjacent_enemy))
                    debug(str(me) + ': Steam-rolling enemy' + str(minhp(adjacent_enemy)))

                elif minhp(adjacent_enemy) in fighting and me not in taken_moves:
                    target = minhp(adjacent_enemy)
                    move = staying('attack',target)
                    debug(str(me) + ': Helping teammate attack enemy ' + str(target))   

                elif safemove:

                    target = minhp(adjacent_enemy)
                    if robots[target].hp < attack_damage and robots[me].hp < 15 and target in chasing:
                        move = moving(me,mindist(safemove,team_center),True)
                        debug(str(me) + ': Someone else is chasing. Too risky to be close.')

                    elif (robots[target].hp < robots[me].hp or target in spawn) and me not in taken_moves:
                        move = staying('attack',target)
                        fighting.add(target)
                        debug(str(me) + ': Trading hits with enemy ' + str(target))

                    else:
                        move = moving(me,mindist(safemove,team_center),True)
                        debug(str(me) + ': Run safely to center ' + str(team_center))

                elif semisafemove and me in taken_moves:
                    move = moving(me,mindist(semisafemove,team_center))
                    debug(str(me) + ': I''ve been evicted! Semisafe move to center ' + str(team_center))

                else:
                    target = minhp(adjacent_enemy)
                    move = staying('attack',target)
                    fighting.add(target)
                    debug(str(me) + ': Attacking lowest enemy ' + str(target))

            elif adjacent_enemy2 - team - taken_moves:

                if closest_enemy in fighting and robots[me].hp > attack_damage:
                    move = moving(me,mindist(adjacent_enemy2 - team - taken_moves,closest_enemy))
                    debug(str(me) + ': Moving to help fight enemy ' + str(closest_enemy))

                elif me in taken_moves:
                    move = moving(me,mindist(adjacent_enemy2 - team - taken_moves,closest_enemy))
                    debug(str(me) + ': Moving out of the way and into danger...' + str(closest_enemy))

                else:
                    move = staying('attack',random.sample(adjacent_enemy2 - team - taken_moves,1).pop())
                    debug(str(me) + ': Attacking towards enemies ')

            elif safemove:
                    #debug(safemove)
                    move = moving(me,mindist(safemove,closest_fighting),True)
                    debug(str(me) + ': Moving safely to enemy' + str(closest_fighting)) 

            else:
                 move = staying('guard')
                 debug(str(me) + ': fell through, guarding...')

            return move


        # Used to make the code a little more readable
        robots = game.robots

        #====================================
        #=========  GLOBAL SETS  ============
        #====================================

        team = set([bot for bot in robots if robots[bot].player_id==self.player_id])
        enemy = set(robots)-team

        sum_x = 0
        sum_y = 0
        for x, y in team:
            sum_x = sum_x + x
            sum_y = sum_y + y
        team_center = (sum_x/len(team), sum_y/len(team))


        global turn_number, turns_till_spawn, taken_moves, freed_moves, fighting, chasing, moves, priorities, coords, sorted_scores, had_turn
        if game.turn != turn_number:
            turn_number = game.turn

            if turn_number > 90:
                turns_till_spawn = 10
            else:
                turns_till_spawn = 10 - turn_number%10

            taken_moves = set()
            freed_moves = set()
            fighting = set()
            chasing = set()
            had_turn = set()

            nTeam = len(team)
            radius = 7
            coords = circle(radius, nTeam)
            

            enemy_scores = {}
            for loc in enemy:
                enemy_scores[loc] = score_enemy(loc)
                if enemy_scores[loc] > 200:
                    fighting.add(loc)
                    debug('fighting -> ' + str(loc))

            sorted_scores = sorted(enemy_scores.iteritems(), key=operator.itemgetter(1), reverse=True)

            priorities = {}
            
            for loc in team:
                priorities[loc] = determine_priority(loc)

            sorted_priorities = sorted(priorities.iteritems(), key=operator.itemgetter(1), reverse=True)

            # print sorted_priorities
            moves = {}
            for loc, value in sorted_priorities:
                moves[loc] = determine_move(loc)
                had_turn.add(loc)

            debug('Scores: ' + str(sorted_scores)) 
            debug('Fighting: ' + str(fighting))

            debug(team)
            debug(enemy)

            total_damage_dealt = 50*5*int(ceil(turn_number/10.0))
            for i in enemy:
                total_damage_dealt = total_damage_dealt - robots[i].hp
            debug('Hive damage dealt: ' + str(total_damage_dealt))

            total_damage_taken = 50*5*int(ceil(turn_number/10.0))
            for i in team:
                total_damage_taken = total_damage_taken - robots[i].hp
            debug( 'Hive damage taken: ' + str(total_damage_taken))

        t1 = time()
        time_diff = (t1-t0)*1000
        debug('Time: %f ms' %time_diff)

        return moves[self.location]