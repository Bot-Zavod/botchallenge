#! /usr/bin/env python3


from math import sqrt
from element import Element
import re
from typing import Tuple

class Node():
    """A node class for A* Pathfinding"""

    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position
    
    def __str__(self):
        return str(self.position)
    
    def __repr__(self):
        return str(self.position)

class Board:
    COUNT_LAYERS = 3
    INPUT_REGEX = "(.*),\"layers\":\[(.*)\](.*)"

    def __init__(self, input):
        matcher = re.search(Board.INPUT_REGEX, input)
        board_string = matcher.group(2).replace('\n', '').replace(',', '').replace('\"', '')  # one line board

        self._board = []
        _layer_len = int(len(board_string) / Board.COUNT_LAYERS)
        for i in range(Board.COUNT_LAYERS):
            _layer = []
            for j in range(_layer_len):
                _layer.append(board_string[j + (i * _layer_len)])
            self._board.append(_layer)
        self._layer_size = int(sqrt(_layer_len))

        self._jump_over = self.jump_over()
        self._non_barrier = self.non_barrier()

    def _find_all(self, element):
        _points = []
        _a_char = element.get_char()
        for i in range(len(self._board)):
            for j in range(len(self._board[i])):
                if self._board[i][j] == _a_char:
                    _points.append(self._strpos2pt(j))
        return _points

    def _strpos2pt(self, strpos):
        return tuple(self._strpos2xy(strpos))

    def _strpos2xy(self, strpos):
        return strpos % self._layer_size, strpos // self._layer_size

    def get_at(self, x, y):
        _strpos = self._xy2strpos(x, y)
        _elements = []
        for i in range(len(self._board)):
            _elements.append(Element(self._board[i][_strpos]))
        return _elements

    def _xy2strpos(self, x, y):
        return self._layer_size * y + x

    def is_at(self, x, y, element_object):
        return element_object in self.get_at(x, y)

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
        # points.update(self.get_holes())
        # points.update(self.get_empty())        
        points.update(self.get_lasers())
        points.update(self.get_other_heroes())
        points.add(self.get_hero()) # single tuple
        return points
    
    def jump_over(self):
        points = set()
        points.update(self.get_holes())
        points.update(self.get_boxes())
        # points.update(self.get_other_heroes())
        points.update(self.get_laser_machines())
        lasers = self.check_lasers()
        if lasers:
            points.update(lasers)
        points.update(self.check_danger_enemies())
        return points

    def check_lasers(self):
        points = set()
        #Calculate all points for next Lasers
        
        possible_lasers = ('LASER_LEFT', 'LASER_RIGHT', 'LASER_UP', 'LASER_DOWN')
        charged_guns = ('LASER_MACHINE_READY_LEFT', 'LASER_MACHINE_READY_RIGHT', 'LASER_MACHINE_READY_UP', 'LASER_MACHINE_READY_LEFT')
        actions = ((-1,0), (1,0), (0,-1), (0,1))
        for laser_dir, machine, action in zip(possible_lasers, charged_guns, actions):
            lasers = self._find_all(Element(laser_dir))
            lasers += self._find_all(Element(machine))
            points.update((laser[0] + action[0], laser[1] + action[1]) for laser in lasers)
        return points

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

    def get_hero(self):
        points = set()
        points.update(self._find_all(Element('ROBO_FALLING')))
        points.update(self._find_all(Element('ROBO_LASER')))
        points.update(self._find_all(Element('ROBO')))
        points.update(self._find_all(Element('ROBO_FLYING')))
        assert len(points) <= 1, "There should be only one robo"
        return list(points)[0]

    def is_me_alive(self):
        points = set()
        points.update(self._find_all(Element('ROBO_FALLING')))
        points.update(self._find_all(Element('ROBO_LASER')))
        return len(points) == 0

    def get_other_heroes(self):
        points = set()
        points.update(self._find_all(Element('ROBO_OTHER_FALLING')))
        points.update(self._find_all(Element('ROBO_OTHER_LASER')))
        points.update(self._find_all(Element('ROBO_OTHER')))
        points.update(self._find_all(Element('ROBO_OTHER_FLYING')))
        return list(points)

    def get_empty(self):
        return self._find_all(Element('EMPTY'))

    def get_zombies(self):
        points = set()
        points.update(self._find_all(Element('FEMALE_ZOMBIE')))
        points.update(self._find_all(Element('MALE_ZOMBIE')))
        points.update(self._find_all(Element('ZOMBIE_DIE')))
        return list(points)

    def get_laser_machines(self):
        points = set()
        points.update(self._find_all(Element('LASER_MACHINE_CHARGING_LEFT')))
        points.update(self._find_all(Element('LASER_MACHINE_CHARGING_RIGHT')))
        points.update(self._find_all(Element('LASER_MACHINE_CHARGING_UP')))
        points.update(self._find_all(Element('LASER_MACHINE_CHARGING_DOWN')))
        points.update(self._find_all(Element('LASER_MACHINE_READY_LEFT')))
        points.update(self._find_all(Element('LASER_MACHINE_READY_RIGHT')))
        points.update(self._find_all(Element('LASER_MACHINE_READY_UP')))
        points.update(self._find_all(Element('LASER_MACHINE_READY_DOWN')))
        return list(points)

    def get_lasers(self):
        points = set()
        points.update(self._find_all(Element('LASER_LEFT')))
        points.update(self._find_all(Element('LASER_RIGHT')))
        points.update(self._find_all(Element('LASER_UP')))
        points.update(self._find_all(Element('LASER_DOWN')))
        return list(points)

    def get_boxes(self):
        return self._find_all(Element('BOX'))

    def get_floors(self):
        return self._find_all(Element('FLOOR'))

    def get_holes(self):
        points = set()
        points.update(self._find_all(Element('HOLE')))
        points.update(self._find_all(Element('ROBO_FALLING')))
        points.update(self._find_all(Element('ROBO_OTHER_FALLING')))
        return list(points)

    def get_exits(self):
        return self._find_all(Element('EXIT'))

    def get_starts(self):
        return self._find_all(Element('START'))

    def get_golds(self):
        return self._find_all(Element('GOLD'))

    def get_walls(self):
        points = set()
        points.update(self._find_all(Element('ANGLE_IN_LEFT')))
        points.update(self._find_all(Element('WALL_FRONT')))
        points.update(self._find_all(Element('ANGLE_IN_RIGHT')))
        points.update(self._find_all(Element('WALL_RIGHT')))
        points.update(self._find_all(Element('ANGLE_BACK_RIGHT')))
        points.update(self._find_all(Element('WALL_BACK')))
        points.update(self._find_all(Element('ANGLE_BACK_LEFT')))
        points.update(self._find_all(Element('WALL_LEFT')))
        points.update(self._find_all(Element('WALL_BACK_ANGLE_LEFT')))
        points.update(self._find_all(Element('WALL_BACK_ANGLE_RIGHT')))
        points.update(self._find_all(Element('ANGLE_OUT_RIGHT')))
        points.update(self._find_all(Element('ANGLE_OUT_LEFT')))
        points.update(self._find_all(Element('SPACE')))
        return list(points)

    def get_perks(self):
        points = set()
        points.update(self._find_all(Element('UNSTOPPABLE_LASER_PERK')))
        points.update(self._find_all(Element('DEATH_RAY_PERK')))
        points.update(self._find_all(Element('UNLIMITED_FIRE_PERK')))
        return list(points)

    # def is_near(self, x, y, elem):
    #     _is_near = False
    #     if not Point(x, y).is_bad(self._layer_size):
    #         _is_near = (self.is_at(x + 1, y, elem) or
    #                     self.is_at(x - 1, y, elem) or
    #                     self.is_at(x, 1 + y, elem) or
    #                     self.is_at(x, 1 - y, elem))
    #     return _is_near

    # def count_near(self, x, y, elem):
    #     _near_count = 0
    #     if not Point(x, y).is_bad(self._layer_size):
    #         for _x, _y in ((x + 1, y), (x - 1, y), (x, 1 + y), (x, 1 - y)):
    #             if self.is_at(_x, _y, elem):
    #                 _near_count += 1
    #     return _near_count

    def to_string(self):
        return ("Board:\n{brd}\nHero at: {hero}\nOther Heroes "
                "at: {others}\nZombies at: {zmb}\nLasers at:"
                " {lsr}\nHoles at : {hls}\nGolds at: "
                "{gld}\nPerks at: {prk}".format(brd=self._line_by_line(),
                                                  hero=self.get_hero(),
                                                  others=self.get_other_heroes(),
                                                  zmb=self.get_zombies(),
                                                  lsr=self.get_lasers(),
                                                  hls=self.get_holes(),
                                                  gld=self.get_golds(),
                                                  prk=self.get_perks())
                )

    def _line_by_line(self):
        _string_board = '  '
        for i in range(self._layer_size * Board.COUNT_LAYERS):
            _string_board += str(i % 10)
            if (i + 1) % self._layer_size == 0:
                _string_board += '\t'

        _string_board += '\n'

        for i in range(self._layer_size):
            _string_board += str(i % 10) + ' '
            for j in range(Board.COUNT_LAYERS):
                for k in range(self._layer_size):
                    _string_board += self._board[j][k + (i * self._layer_size)]
                _string_board += '\t'
            _string_board += '\n'

        return _string_board
  
    #Pathfinding methods of the board

    def bfs_nearest(self, start: tuple, end_points: list):
        print(end_points)
        """ return the nearest point to the start """
        
        visited = set() 
        queue = [start]
        
        while queue:
            node = queue.pop()
            visited.add(node)
            
            neighbors = self._get_neighbors(node)
            for neighbor in neighbors:
                if neighbor not in visited:
                    if neighbor in end_points:
                        return neighbor
                    queue.append(neighbor)
        return None


    def astar(self, start: tuple, end: tuple):
            """Returns a list of tuples as a path from the given start to the given end in the given maze"""

            # Create start and end node
            start_node = Node(None, start)
            start_node.g = start_node.h = start_node.f = 0
            end_node = Node(None, end)
            end_node.g = end_node.h = end_node.f = 0

            # Initialize both open and closed list
            open_list = []
            closed_list = []

            # Add the start node
            open_list.append(start_node)

            # Loop until you find the end
            while len(open_list) > 0:
                # print()
                # print("open_list: ", open_list)
                # print("closed_list: ", closed_list)

                # Get the current node
                current_node = open_list[0]
                current_index = 0
                for index, item in enumerate(open_list):
                    if item.f < current_node.f:
                        current_node = item
                        current_index = index
                # print("current_node: ", current_node.position)

                # Pop current off open list, add to closed list
                open_list.pop(current_index)
                closed_list.append(current_node)

                # Found the goal
                if current_node == end_node:
                    path = []
                    current = current_node
                    while current is not None:
                        path.append(current.position)
                        current = current.parent
                    return path[::-1] # Return reversed path

                neighbors = self._get_neighbors(current_node.position)
                # Generate children
                children = []
                for neighbor in neighbors:
                    new_node = Node(current_node, neighbor)  # Create new node
                    children.append(new_node)  # Append

                # Loop through children
                for child in children:
                    
                    stop_itaration = False
                    # Child is on the closed list
                    for closed_child in closed_list:
                        if child == closed_child:
                            stop_itaration = True
                            break
                    if stop_itaration:
                        continue

                    # Create the f, g, and h values
                    child.g = current_node.g + 1
                    if abs((current_node.position[0] - child.position[0]) + (current_node.position[1] - child.position[1])) > 1:
                        child.g += 1
                    child.h = ((child.position[0] - end_node.position[0]) ** 2) + ((child.position[1] - end_node.position[1]) ** 2)
                    child.f = child.g + child.h

                    # Child is already in the open list
                    for open_node in open_list:
                        if child == open_node and child.g > open_node.g:
                            stop_itaration = True
                            break
                    if stop_itaration:
                        continue

                    # Add the child to the open list
                    open_list.append(child)

    def _get_neighbors(self, start: Tuple[int, int]):
        """ return 4 Adjacent squares """

        non_barrier = self._non_barrier
        jump_over = self._jump_over

        neighbors = []
        for new_position in [(0, -1), (1, 0), (0, 1), (-1, 0)]: # Adjacent squares

            # Get node position
            node_position = (start[0] + new_position[0], start[1] + new_position[1])

            # where to jump if it is box or hole
            if node_position in jump_over:
                node_position = (start[0] + new_position[0]*2, start[1] + new_position[1]*2)
            
            # Make sure walkable terrain
            if node_position not in non_barrier:
                continue
            
            # Make sure no object on second layer
            if node_position in jump_over:
                continue
            
            neighbors.append(node_position)
        return neighbors

def mht_dist(start: Tuple[int, int], end: Tuple[int, int]):
    return ((end[0] - start[0]) ** 2) + ((end[1] - start[1]) ** 2)


if __name__ == '__main__':
    raise RuntimeError("This module is not designed to be ran from CLI")


