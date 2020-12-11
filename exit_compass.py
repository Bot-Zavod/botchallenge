import pickle
from os import path

from typing import Tuple


class ExitCompass():
    file_name = "compass.pickle"

    def __init__(self):
        # for reading also binary mode is important
        if path.exists(ExitCompass.file_name):
            # loads adjacencies list from pickle
            with open(ExitCompass.file_name, 'rb') as f:
                self.nav_dict = pickle.load(f)
        else:
            self.nav_dict = dict()

    def pickle_save(self):
        """ saves adjacencies list to pickle """

        with open(ExitCompass.file_name, 'wb') as f:
            pickle.dump(self.nav_dict, f)

    def _comp_path_vec(self, ref: Tuple[int, int],
                       sample: Tuple[int, int]) -> Tuple[int, int]:
        """ vectors substraction """

        return (ref[0] - sample[0], ref[1] - sample[1])

    def calc_vec(self, start: str,
                 rel_pos: Tuple[int, int]) -> Tuple[int, int]:
        """ return nearest exit to player """

        if start not in self.nav_dict:
            return None
        else:
            exit_paths = list(
                filter(lambda x: x[0][0] == "E", self.nav_dict[start])
            )

            shortest_path = float("inf")
            nearest_exit = None
            for i in range(len(exit_paths)):
                exit_path = self._comp_path_vec(exit_paths[i][1], rel_pos)
                manh_path = exit_path[0] ** 2 + exit_path[1] ** 2
                if manh_path < shortest_path:
                    shortest_path = manh_path
                    nearest_exit = exit_paths[i]
            return nearest_exit

    def add_ref_vec(self, source: str, dest: str,
                    ref_vec: Tuple[int, int]) -> None:
        """ rebuild the graph """

        if source not in self.nav_dict:
            self.nav_dict[source] = set()

        new_node = (dest, ref_vec)
        if new_node in self.nav_dict[source]:
            return

        self.nav_dict[source].add(new_node)
        if dest[0][0] == "S":  # bidirectional dependency
            if dest not in self.nav_dict:
                self.nav_dict[dest] = {(dest, (ref_vec[0] * -1,
                                               ref_vec[1] * -1))}

        # append data in referenced nodes
        references = self.nav_dict[source]
        for ref in references:
            if ref[0][0] == "S" and ref[0] != dest:  # if it's new start
                new_ref_vec = self._comp_path_vec(ref_vec, ref[1])
                self.nav_dict[ref[0]].add((dest, new_ref_vec))

        # append data to dest node from referenced nodes
        if dest[0] == "S":
            for ref in references:
                if ref[0] != dest:
                    new_ref_vec = self._comp_path_vec(ref[1], ref_vec)
                    self.nav_dict[dest].add((ref[0], new_ref_vec))
        self.pickle_save()

    def print_dict(self):
        for node in self.nav_dict:
            print(node)
            for child in self.nav_dict:
                print("\t", child)


# compass = ExitCompass()
# print(compass._comp_path_vec((10, -10), (10, -5)))
