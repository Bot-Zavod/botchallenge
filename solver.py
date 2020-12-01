#!/usr/bin/env python3
from typing import List, Set

from board import Board
from command import Command
from element import Element

from astar import Node
from gamepad import GamepadRoboController

""" This class should contain the movement generation algorithm."""
class DirectionSolver:

    def __init__(self):  # initializes on websocket start
        self._board = None
        self._non_barrier = None
        self._board_size = None
        
        self.is_jumping = False
        self.goal = "EXIT"
        
        self.сhache = None

        self.gp = GamepadRoboController()

    def get(self, board_string):
        self._board = Board(board_string)
        self._non_barrier = self._board.non_barrier()
        self._board_size = self._board._layer_size - 1
        return self.next_command()

    """ Implement your logic here """
    
    def _get_neighbors(self, start: tuple):
        """ return 4 Adjacent squares """
        
        size = self._board_size
        non_barrier = self._non_barrier

        neighbors = []
        for new_position in [(0, -1), (1, 0), (0, 1), (-1, 0)]: # Adjacent squares

            # Get node position
            node_position = (start[0] + new_position[0], start[1] + new_position[1])

            # Make sure within range
            if (node_position[0] > size 
                    or node_position[0] < 0
                    or node_position[1] > size
                    or node_position[1] < 0):
                continue

            # Make sure walkable terrain
            if node_position not in non_barrier:
                continue
            
            neighbors.append(node_position)
        return neighbors
    
    def _astar(self, start: tuple, end: tuple):
        """Returns a list of tuples as a path from the given start to the given end in the given maze"""

        maze = self._board
        
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

    def _bfs_nearest(self, start: tuple, end_points: list):
        print(end_points)
        """ return the nearest point to the start """
        
        end_points = {point.get_coord() for point in end_points}
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

    def next_command(self):
        сhache = self.сhache
        board = self._board
        print(board.to_string())
        
        cmd = ''
        if self.is_jumping:
            self.is_jumping = False
        elif False:
            start = board.get_hero().get_coord()
            end_points = board.get_exits()
            golds = board.get_golds()
            
            if golds:
                self.goal = "GOLD"
                end_points = golds
            
            if len(end_points) > 1:
                end = self._bfs_nearest(start, end_points)
            else:
                end = end_points[0].get_coord()
                
            print("end: ", end)
            
            if start != end:
                if сhache:
                    path = сhache
                else:
                    path = self._astar(start, end)
                сhache = path[1:]
                
                # print("path: ", path)
                step = сhache[0]
                
                if step == end:
                    сhache == None
                
                if start[0] > step[0]:
                    cmd += 'LEFT'
                elif start[0] < step[0]:
                    cmd += 'RIGHT'
                elif start[1] > step[1]:
                    cmd += 'UP'
                elif start[1] < step[1]:
                    cmd += 'DOWN'
                    
                if board.is_at(*step, Element('HOLE')):
                    cmd = f"ACT(1),{cmd}"
                    self.is_jumping = True
        cmd = self.gp.get_action_code()
        _command = Command(cmd)
        print("Sending Command: {}\n".format(_command.to_string()))
        return _command.get_command()


if __name__ == '__main__':
    raise RuntimeError("This module is not intended to be ran from CLI")
