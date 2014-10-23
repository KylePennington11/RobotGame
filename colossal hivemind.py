# Learned syntax from Simplebot by ramk13

import rg, random, operator
from time import time
from math import sqrt,sin,cos,pi,ceil

class Robot:

    SPAWN_INTERVAL = rg.settings.spawn_every            # how many turns pass between robots being spawned
    SPAWN_PER_PLAYER = rg.settings.spawn_per_player     # how many robots are spawned per player
    ROBOT_HP = rg.settings.robot_hp                     # default robot HP
    ATTACK_RANGE = rg.settings.attack_range
    COLLISION_DAMAGE = rg.settings.collision_damage     # damage dealt by collisions
    SUICIDE_DAMAGE = rg.settings.suicide_damage         # damage dealt by suicides
    MAX_TURNS = rg.settings.max_turns
    ATTACK_DAMAGE = 10
    SPAWN = set(rg.settings.spawn_coords)
    OBSTACLES = set(rg.settings.obstacles)
    CENTER = rg.CENTER_POINT

    AROUND_SPAWN = set()
    for i in SPAWN:
        points = set(rg.locs_around(i))
        AROUND_SPAWN = AROUND_SPAWN | (points - SPAWN - OBSTACLES)

    debug_enabled = True

    #====================================
    #============  VARIABLES  ===========
    #==================================== 
    #global turn_number, turns_till_spawn, taken_moves, freed_moves, fighting, chasing, moves, priorities, coords, sorted_scores, had_turn
    had_turn = set()
    taken_moves = set()
    freed_moves = set()
    moves = {}

    fighting = set()

    robots = ()
    enemy = set()
    team = set()

    turn_number = -1

    team_center = CENTER


    #====================================
    #============  FUNCTIONS  ===========
    #====================================  

    def debug(self, text):
        if self.debug_enabled:
            print text
            
    def around(self, (x,y),radius=1):
        points = set()
        for i in xrange(radius+1):
            points.add((-i+x,-radius+i+y))
            points.add((-i+x,radius-i+y))
            points.add((i+x,-radius+i+y))
            points.add((i+x,radius-i+y))
        return points - self.OBSTACLES

    def diag_around(self, (x,y)):
        offsets = ((1, 1), (1, -1), (-1, 1), (-1, -1))
        return set([(x + dx, y + dy) for dx, dy in offsets]) - self.OBSTACLES

    # def circle(self, radius, n):
    #     circle_coords = set()
    #     for i in range(n):
    #         theta = i*2*pi/float(n)
    #         x = int(radius*sin(theta)) + 9
    #         y = int(radius*cos(theta)) + 9
    #         coord = (x,y)
    #         circle_coords.add(coord)
    #     return circle_coords

    def min_dist (self, bots, loc):
        return min(bots,key=lambda x:rg.dist(x, loc))


    #====================================
    #==========  PICK TARGET  ===========
    #====================================
    def score_enemy(self, loc):
        # the bigger the more screwed they are...
        adjacent = self.around(loc)
        enemy_not_me = self.enemy - set([loc])

        adjacent_team = adjacent & self.team
        adjacent_team2 = self.around(loc,2) & self.team

        adjacent_enemy = adjacent & enemy_not_me

        safemove = adjacent - adjacent_team - adjacent_team2 - self.SPAWN - self.enemy
        semisafemove = adjacent & adjacent_team2
        spawnmoves = (adjacent & self.SPAWN) - adjacent_team - self.enemy

        hp_score = self.robots[loc].hp*2

        score = len(adjacent_enemy)*20 + len(safemove)*50 +  len(semisafemove)*10 + len(spawnmoves)*5 + hp_score

        return 300 - score


    #====================================
    #============  PRIORITY  ============
    #====================================            
    def determine_priority(self, loc):
        adjacent = self.around(loc)
        adjacent_enemy = adjacent & self.enemy
        near_enemy = self.around(loc,2) & self.enemy
        adjacent_team = adjacent & self.team

        in_spawn = self.SPAWN & set([loc])

        points_spawn = 10*len(in_spawn)*(11-self.turns_till_spawn)
        points_enemies = 15*len(adjacent_enemy)
        points_enemies = points_enemies + 5*len(near_enemy)
        points_team = 5*len(adjacent_team)
        points_hp = (500 - self.robots[loc].hp*10)/10

        priority = points_spawn + points_enemies + points_team + points_hp

        #debug(str(loc) + ': ' + str(priority) + ' || ' + str(points_spawn) + ' - ' + str(points_enemies) + ' - ' + str(points_team) + ' - ' + str(points_hp))

        return priority


    #====================================
    #========  DETERMINE MOVE  ==========
    #====================================
    def determine_move(self, loc):

        #====================================
        #=============  SETS  ===============
        #====================================


        me = loc
        team_not_me = self.team - set([me])

        adjacent = self.around(me)

        adjacent_enemy = adjacent & self.enemy
        adjacent_enemy2 = set(filter(lambda k:self.around(k) & self.enemy, adjacent))

        adjacent_team = adjacent & team_not_me
        adjacent_team2 = set(filter(lambda k:self.around(k) & team_not_me, adjacent))
        adjacent_team_blocking = adjacent_team - self.SPAWN - self.had_turn

        safemove           = adjacent-adjacent_enemy-adjacent_enemy2-self.SPAWN-(self.team-self.freed_moves)-self.taken_moves
        semisafemove       = adjacent-adjacent_enemy                -self.SPAWN-(self.team-self.freed_moves)-self.taken_moves
        safemove_withspawn = adjacent-adjacent_enemy-adjacent_enemy2      -(self.team-self.freed_moves)-self.taken_moves
        semisafemove_spawn = adjacent-adjacent_enemy                      -(self.team-self.freed_moves)-self.taken_moves

        if self.enemy:
            closest_enemy = self.min_dist(self.enemy,me)
        else:
            closest_enemy = self.CENTER

        if self.fighting:
            closest_fighting = self.min_dist(self.fighting,me)
        else:
            closest_fighting = closest_enemy

        if team_not_me:
            closest_team = self.min_dist(team_not_me,me)
        else:
            closest_team = self.CENTER

        # if coords:
        #     closest_coord = self.min_dist(coords,me)
        #     coords.remove(closest_coord)
        # else:
        #     closest_coord = center

        if self.turns_till_spawn == 0:
            for s in self.SPAWN:
                self.taken_moves.add(s)


        #====================================
        #=========== LOGIC ==================
        #====================================

        if self.robots[me].hp <= self.ATTACK_DAMAGE and adjacent_enemy and (safemove | safemove_withspawn):
            self.debug(str(me) + ': Fleeing. ')
            return self.moving(me, self.min_dist(safemove | safemove_withspawn, self.team_center), True)

        elif len(adjacent_enemy) == 1 and self.robots[me].hp >= self.robots[self.minhp(adjacent_enemy)].hp:
            self.debug(str(me) + ': Attacking weak enemy. ')
            self.fighting.add(self.minhp(adjacent_enemy))
            return self.staying('attack', self.minhp(adjacent_enemy))

        elif adjacent_enemy & self.fighting:
            self.debug(str(me) + ': Attacking enemy fighting. ')
            return self.staying('attack', self.min_dist(adjacent, self.minhp(adjacent_enemy & self.fighting)))

        elif self.around(me, 2) & self.fighting and (safemove | semisafemove | safemove_withspawn | semisafemove_spawn):
            self.debug(str(me) + ': Moving towards enemies2 to help. ')
            return self.moving(me, self.min_dist(safemove | semisafemove | safemove_withspawn | semisafemove_spawn, self.minhp(self.around(me, 2) & self.fighting)), True)

        elif self.around(me, 3) & self.fighting and (safemove | semisafemove | safemove_withspawn | semisafemove_spawn):
            self.debug(str(me) + ': Moving towards enemies3 to help. ')
            return self.moving(me, self.min_dist(safemove | semisafemove | safemove_withspawn | semisafemove_spawn, self.minhp(self.around(me, 3) & self.fighting)), True)

        elif me in self.AROUND_SPAWN and (adjacent_team or adjacent_team2) and me not in self.taken_moves and (adjacent - team_not_me):
            if adjacent_enemy:
                self.fighting.add(closest_enemy)
            self.debug(str(me) + ': Attacking towards enemies ')
            return self.staying('attack', self.min_dist(adjacent - team_not_me, closest_enemy))

        elif safemove:           
            closest_spawn = self.min_dist(self.AROUND_SPAWN - self.enemy - self.team - self.taken_moves, closest_team)
            self.debug(str(me) + ': Moving safely to ' + str(closest_spawn))
            return self.moving(me, self.min_dist(safemove, closest_spawn), True)

        elif semisafemove:
            closest_spawn = self.min_dist(self.AROUND_SPAWN - self.enemy - self.team - self.taken_moves, closest_team)
            self.debug(str(me) + ': Moving semi-safely to ' + str(closest_spawn))
            return self.moving(me, self.min_dist(semisafemove, closest_spawn), False)

        elif adjacent_team_blocking:
            self.debug(str(me) + ': Pushing teammate ' + str(adjacent_team_blocking))
            return self.moving(me, self.min_dist(adjacent_team_blocking, me), False)

        elif safemove_withspawn:
            closest_spawn = self.min_dist(self.AROUND_SPAWN - self.enemy - self.team - self.taken_moves, closest_team)
            self.debug(str(me) + ': Moving safely through spawn to ' + str(closest_spawn))
            return self.moving(me, self.min_dist(safemove_withspawn, closest_spawn), True)
         
        else:
            self.debug(str(me) + ': Guarding')
            return self.staying('guard', me)


    def evaluate_moves(self, me):

        team_not_me = self.team - set([me])

        


        return 13

                  # If moving save the location we are moving to 
    def moving(self, me, loc, guaranteed=True):
        self.taken_moves.add(loc)
        if guaranteed:
            self.freed_moves.add(me)
        return ['move', loc]

    # If staying save the location that we are at
    def staying(self, act, loc=CENTER):
        return [act, loc]
        
    # Function to find bot with the least health
    def minhp (self, bots):
        return min(bots,key=lambda x:self.robots[x].hp)

    def update_team_centre(self):
        sum_x = 0
        sum_y = 0
        for x, y in self.team:
            sum_x = sum_x + x
            sum_y = sum_y + y
        self.team_center = (sum_x/len(self.team), sum_y/len(self.team))        

    def act(self, game):
        t0 = time()

        # Used to make the code a little more readable
        self.robots = game.robots

        #====================================
        #=========  GLOBAL SETS  ============
        #====================================

        self.team = set([bot for bot in self.robots if self.robots[bot].player_id==self.player_id])
        self.enemy = set(self.robots) - self.team


        if game.turn != self.turn_number:
            self.turn_number = game.turn

            if self.turn_number > 90:
                self.turns_till_spawn = 10
            else:
                self.turns_till_spawn = 10 - self.turn_number%10


            self.life_support = set()
            self.taken_moves = set()
            self.freed_moves = set()
            self.fighting = set()
        #     self.chasing = set()
            self.had_turn = set()  

            self.update_team_centre()        

            enemy_scores = {}
            for loc in self.enemy:
                enemy_scores[loc] = self.score_enemy(loc)
        #    if enemy_scores[loc] > 200:
        #        self.fighting.add(loc)
        #        self.debug('fighting -> ' + str(loc))

            sorted_scores = sorted(enemy_scores.iteritems(), key=operator.itemgetter(1), reverse=True)

            self.debug('Enemy:')
            self.debug(sorted_scores)

            evaluations = {}
            for loc in self.team:
                evaluations[loc] = self.evaluate_moves(loc)


            self.debug('Evaluations: ' + str(evaluations))

            priorities = {}
            
            for loc in self.team:
                priorities[loc] = self.determine_priority(loc)

            sorted_priorities = sorted(priorities.iteritems(), key=operator.itemgetter(1), reverse=True)

            self.debug('Team:')
            self.debug(sorted_priorities)

            self.debug('')

            self.moves = {}
            for loc, value in sorted_priorities:
                self.moves[loc] = self.determine_move(loc)



        #     debug('Scores: ' + str(sorted_scores)) 
            self.debug('Fighting: ' + str(self.fighting))

        #     print team
        #     print enemy

        #     total_damage_dealt = 50*5*int(ceil(turn_number/10.0))
        #     for i in enemy:
        #         total_damage_dealt = total_damage_dealt - robots[i].hp
        #     debug('Hive damage dealt: ' + str(total_damage_dealt))

        #     total_damage_taken = 50*5*int(ceil(turn_number/10.0))
        #     for i in team:
        #         total_damage_taken = total_damage_taken - robots[i].hp
        #     debug( 'Hive damage taken: ' + str(total_damage_taken))
            self.debug('')
            self.debug(str(len(self.team)) + ' v ' + str(len(self.enemy)))

        t1 = time()
        time_diff = (t1-t0)*1000
        self.debug('Time: %f ms' %time_diff)

        

        return self.moves[self.location]