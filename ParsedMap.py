from typing import Dict, FrozenSet
from zone import Zone


class Parsed_Map:
    """
    Container for holding parsed map elements and flight configuration data.

    Args:
        nb_drones (int): Total number of drones to route in the simulation.
        start_hub (str): Name of the starting node hub.
        end_hub (str): Name of the destination target node hub.
        zones (Dict[str, Zone]):
            Mapping of zone name strings to Zone instances.
        connections (Dict[FrozenSet[str], int]):
            Mapping of zone pairs to link capacities.
    """
    def __init__(
        self,
        nb_drones: int,
        start_hub: str,
        end_hub: str,
        zones: Dict[str, Zone],
        connections: Dict[FrozenSet[str], int]
    ) -> None:
        """
        Initializes the parsed map data structure with configuration limits.
        """
        self.nb_drones = nb_drones
        self.start_hub = start_hub
        self.end_hub = end_hub
        self.zones = zones
        self.connections = connections
