from typing import Tuple, List, Set
from element import Element


class Mixin:
    
    def get_actionspace(self) -> Set[Tuple[int, int]]:
        hero = self._hero
        lasers = self.check_first_lasers()
        actions = ((-1,0), (1,0), (0,-1), (0,1), (0,0))
        
        first_lasers = set(lasers[0] + lasers[1] + lasers[2] + lasers[3])
        second_lasers = self.check_second_lasers()
        
        hero_step = {(hero[0] + act[0], hero[1] + act[1]) for act in actions}
        hero_jump = {(hero[0] + act[0]*2, hero[1] + act[1]*2) for act in actions}
        
        laser_actionspace = (hero_step - first_lasers).union(hero_jump - second_lasers)
        
        return laser_actionspace
    
    def is_barrier_at(self, x, y):
        points = self.non_barrier()
        return (x, y) not in points
    
    def non_barrier(self):
        # returns set of non barrier coordinates
        points = set()
        points.update(self.get_floors())
        points.update(self.get_starts())
        points.update(self.get_exits())
        points.update(self.get_golds())
        points.update(self.get_other_heroes())
        points.add(self.get_hero()) # single tuple
        return points
    
    def second_layer_barrier(self):
        points = set()
        points.update(self.get_laser_machines())
        points.update(self.get_boxes())
        return points
    
    def jump_over(self):
        points = set()
        points.update(self.get_holes())
        points.update(self.get_boxes())
        points.update(self.get_laser_machines())
        # lasers = self.check_first_lasers()
        # lasers = lasers[0] + lasers[1] + lasers[2] + lasers[3]
        # if lasers:
        #     points.update(set(lasers))
        # points.update(self.check_danger_enemies())
        return points

    def check_first_lasers(self) -> List[Set[Tuple[int, int]]]:
        # step is predicting lasers on specific sec
        points = [list()]*4  # left, right, up, down
        #Calculate all points for next Lasers
        
        possible_lasers = ('LASER_LEFT', 'LASER_RIGHT', 'LASER_UP', 'LASER_DOWN')
        charged_guns = ('LASER_MACHINE_READY_LEFT', 'LASER_MACHINE_READY_RIGHT', 
                        'LASER_MACHINE_READY_UP', 'LASER_MACHINE_READY_DOWN')
        actions = ((-1,0), (1,0), (0,-1), (0,1))
        for i, laser_dir, machine, action in zip(
                    range(3), possible_lasers, charged_guns, actions):
            lasers = self._find_all(Element(laser_dir)) + self._find_all(Element(machine))
            points[i] = [(laser[0] + action[0], laser[1] + action[1]) for laser in lasers]
        return points
    
    def check_second_lasers(self) -> Set[Tuple[int, int]]:
        first_lasers = self.check_first_lasers()
        second_layer_barrier = self.second_layer_barrier()
        actions = ((-1,0), (1,0), (0,-1), (0,1))
        second_lasers = set()
        
        for i, lasers in enumerate(first_lasers):
            for laser in lasers:
                if laser not in second_layer_barrier:
                    second_lasers.add(
                        (laser[0] + actions[i][0], laser[1] + actions[i][1])
                    )
        return second_lasers

    def check_danger_enemies(self):
        points = set()
        hero_coords = self.get_hero()
        #Check if zombies are anywhere near      
        possible_zombies = ('FEMALE_ZOMBIE', 'FEMALE_ZOMBIE')
        actions = ((-1,0), (1,0), (0,-1), (0,1), (0,0))

        zombie_moves = set()
        zombies = self._find_all(Element(possible_zombies[0])) + self._find_all(Element(possible_zombies[1]))
        for zombie in zombies:
            for action in actions:
                zombie_moves.add((zombie[0] + action[0], zombie[1] + action[1]))

        player_moves = set()
        for action in actions[:-1]:
            player_moves.add((hero_coords[0] + action[0], hero_coords[1] + action[1]))
            player_moves.add((hero_coords[0] + action[0]*2, hero_coords[1] + action[1]*2))
            
        points = player_moves & zombie_moves    

        return points    

    def is_me_alive(self) -> bool:
        points = set()
        points.update(self._find_all(Element('ROBO_FALLING')))
        points.update(self._find_all(Element('ROBO_LASER')))
        return len(points) == 0
