from ParsedMap import Parsed_Map
from drone import Drone
from typing import Any, Optional
import heapq


class Graph:
    """
    Manages spatial graph topologies and multi-agent space-time reservations.

    Args:
        Map (Parsed_Map): The parsed map topology containing hubs and links.
    """
    def __init__(self, Map: Parsed_Map):
        """
        Initializes the simulation environment and reservation tables.
        """
        self.nb_drones = Map.nb_drones
        self.start = Map.start_hub
        self.end = Map.end_hub
        self.zones_details = Map.zones
        self.zones_link = Map.connections
        self.adjacent: dict[str, list[str]] = {
            name: [] for name in Map.zones
        }
        self.res_nodes: dict[tuple[str, int], int] = {}
        self.res_link: dict[tuple[str, int], int] = {}
        self.drone_list = self._get_drone_list_()

    def _get_drone_list_(self) -> list[Drone]:
        """
        Generates a sequential list of Drone instances.

        Returns:
            list[Drone]: Generated drone agents.
        """
        return [Drone(i + 1) for i in range(0, self.nb_drones)]

    def build_adjacent(self) -> bool:
        """Constructs an adjacency list filtering out blocked zones.

        Returns:
            bool: True if the graph layout is fully connected and valid,
                  False if ANY zone (including middle hubs) is stranded.
        """
        for frozen_key in self.zones_link.keys():
            zones = list(frozen_key)
            if len(zones) != 2:
                continue
            z1, z2 = zones
            is_z1_blocked = self.zones_details[z1].zone_type == "blocked"
            is_z2_blocked = self.zones_details[z2].zone_type == "blocked"
            if is_z1_blocked or is_z2_blocked:
                continue

            self.adjacent[z1].append(z2)
            self.adjacent[z2].append(z1)

        if not self.adjacent.get(self.start):
            print(f"[ERROR] Start hub"
                  f"'{self.start}' has no operational connections.")
            return False
        if not self.adjacent.get(self.end):
            print(f"[ERROR] End ``hub '{self.end}'"
                  f"has no operational connections.")
            return False

        for name, neighbors in self.adjacent.items():
            if len(neighbors) == 0:
                print(f"[ERROR] Map contains a stranded zone: '{name}'"
                      f" is not connected to anything.")
                return False

        return True

    def run_all_drones(self) -> dict[int, list[str]]:
        """
        Coordinates pathfinding sequentially for all drones.

        Returns:
            dict[int, list[str]]: Map of drone IDs to their calculated paths.
        """
        if not self.build_adjacent():
            return {}
        all_results = {}
        blocked = False
        self.res_nodes = {}
        self.res_link = {}

        for drone_obj in self.drone_list:
            path = []
            if not blocked:
                path = self.find_path(self.start, self.end, drone_obj.id)
                if path is None:
                    print("[ERROR] No valid flight path exists!")
            if path and not blocked:
                all_results[drone_obj.id] = path
                drone_obj.path = path
                self.apply_reservations(path)
            else:
                blocked = True
                all_results[drone_obj.id] = [self.start]
                drone_obj.path = [self.start]

        return all_results

    def find_path(self, start: str, end: str, drone_id: int) -> Any:
        """
        Finds a collision-free path for a drone using space-time Dijkstra.

        Args:
            start (str): Start hub name.
            end (str): Destination hub name.
            drone_id (int): ID of the drone being routed.

        Returns:
            Any: List of path tokens if found, otherwise None.
        """
        max_time_horizon = max(
             100, self.nb_drones * 10 + len(self.zones_details) * 5
        )
        pq = [(0.0, 0, start, [start])]
        visited = set()
        while pq:
            cost, t, curr_name, path = heapq.heappop(pq)
            if curr_name == end:
                return path
            if t > max_time_horizon:
                continue
            if (curr_name, t) in visited:
                continue
            visited.add((curr_name, t))
            for neighbor in self.adjacent[curr_name]:
                neighbor_obj = self.zones_details[neighbor]
                zone_name = neighbor_obj.zone_type
                if zone_name == 'blocked':
                    continue
                is_restricted = (zone_name == 'restricted')
                is_priority = (zone_name == 'priority')
                travel_time = neighbor_obj.turn_cost
                arrival_time = t + travel_time
                node_cost = float(travel_time)
                if is_priority:
                    node_cost -= 0.1
                if neighbor in path:
                    node_cost += 20.0
                node_ok = self.is_node_available(neighbor, arrival_time)
                if is_restricted:
                    node_ok = (
                        node_ok and
                        self.is_node_available(neighbor, arrival_time - 1)
                    )
                link_ok = True
                link_obj = self.get_connection_obj((curr_name, neighbor))
                if link_obj:
                    for dt in range(travel_time):
                        if not self.is_link_available(
                            link_obj.name, t + dt + 1, dest_node=neighbor
                        ):
                            link_ok = False
                            break
                else:
                    link_ok = False
                if node_ok and link_ok:
                    if is_restricted:
                        new_path = path + [link_obj.name, neighbor]
                    else:
                        new_path = path + [neighbor]
                    heapq.heappush(
                        pq,
                        (cost + node_cost, arrival_time, neighbor, new_path)
                    )
            if self.is_node_available(curr_name, t + 1):
                heapq.heappush(
                    pq, (cost + 1.5, t + 1, curr_name, path + [curr_name])
                )

        print(
            f"Drone {drone_id}: No valid path found "
            "(Goal is completely unreachable)."
        )
        return None

    def is_node_available(self, node_name: str, time: int) -> bool:
        """
        Checks if a zone node has available capacity at a specific turn.

        Args:
            node_name (str): Name of the zone.
            time (int): Target simulation turn.

        Returns:
            bool: True if available, False otherwise.
        """
        if node_name == self.end or node_name == self.start:
            return True
        node_obj = self.zones_details[node_name]
        current_occupancy = self.res_nodes.get((node_obj.name, time), 0)
        return bool(current_occupancy < node_obj.max_drones)

    def is_link_available(
            self, connection_id: str, time: int, dest_node: str
    ) -> bool:
        """
        Checks if a connection link has available bandwidth at a specific turn.

        Args:
            connection_id (str): Formatted connection string identifier.
            time (int): Target simulation turn.
            dest_node (str): Target destination zone name.

        Returns:
            bool: True if available, False otherwise.
        """
        if not self.is_node_available(dest_node, time):
            return False
        for frozen_key, cap in self.zones_link.items():
            link_name = "-".join(sorted(list(frozen_key)))
            if link_name == connection_id:
                current_usage = self.res_link.get((connection_id, time), 0)
                return bool(current_usage < cap)
        return True

    def get_connection_obj(self, link: str | tuple[str, str]) -> Any:
        """
        Retrieves or builds a mock connection object between two zones.

        Args:
            link (str | tuple[str, str]):
                Tuple pairing or link identifier string.

        Returns:
            Any: Mock connection tracking metadata, or None.
        """
        if isinstance(link, tuple):
            link_fs = frozenset(link)
            if link_fs in self.zones_link:
                class MockConnection:
                    def __init__(
                        self,
                        key: frozenset[str],
                        cap: Optional[int]
                    ):
                        self.name = "-".join(sorted(list(key)))
                        self.connection = tuple(key)
                        self.max_drones = cap if cap is not None else 5
                return MockConnection(link_fs, self.zones_link[link_fs])
        return None

    def apply_reservations(self, path: list[str]) -> None:
        """
        Commits a calculated path's schedule to the global reservation tables.

        Args:
            path (list[str]):
                List of zone names and connections representing a path.
        """
        start_node = self.zones_details[path[0]]
        self.res_nodes[(start_node.name, 0)] = (
            self.res_nodes.get((start_node.name, 0), 0) + 1
        )
        current_time = 0
        i = 1
        while i < len(path):
            from_name = path[i - 1]
            if path[i] in self.zones_details:
                to_name = path[i]
            else:
                if i + 1 >= len(path):
                    break
                to_name = path[i + 1]
                if to_name not in self.zones_details:
                    break
            if from_name == to_name:
                current_time += 1
                self.res_nodes[(to_name, current_time)] = (
                    self.res_nodes.get((to_name, current_time), 0) + 1
                )
                i += 1
                continue
            to_node = self.zones_details[to_name]
            movement = to_node.turn_cost
            link_obj = self.get_connection_obj((from_name, to_name))
            for step in range(movement):
                t = current_time + 1 + step
                self.res_nodes[(to_name, t)] = (
                    self.res_nodes.get((to_name, t), 0) + 1
                )
                if link_obj:
                    self.res_link[(link_obj.name, t)] = (
                        self.res_link.get((link_obj.name, t), 0) + 1
                    )
            current_time += movement
            if path[i] not in self.zones_details:
                i += 2
            else:
                i += 1
