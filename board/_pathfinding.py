""" Pathfinding methods of the board """

from typing import Tuple, List, Set


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


class Mixin:

    def bfs_nearest(self, start: Tuple[int, int], end_points: Set[Tuple[int, int]]) -> Tuple[int, int]:
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
        return ()

    def astar(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
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

    def _get_neighbors(self, start: Tuple[int, int]) -> List[Tuple[int, int]]:
        """ return 4 Adjacent squares """

        non_barrier = self._non_barrier
        jump_over = self._jump_over
        directions = self.directions[:-1]

        neighbors = []
        for new_position in directions: # Adjacent squares

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

    def _mht_dist(self, start: Tuple[int, int], end: Tuple[int, int]):
        return ((end[0] - start[0]) ** 2) + ((end[1] - start[1]) ** 2)