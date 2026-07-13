from typing import Optional, Dict, Set, Tuple, FrozenSet, Any
from zone import Zone
from ParsedMap import Parsed_Map


class Parser:
    """
    Parses drone configuration files and constructs map topologies.

    Args:
        filename (str): Path to the map configuration text file.
    """
    def __init__(self, filename: str) -> None:
        """
        Initializes the parser instance with empty configuration tracking.
        """
        self.filename: str = filename
        self.drones_number: int = 0
        self.start: Optional[str] = None
        self.end: Optional[str] = None
        self.zones: Dict[str, Zone] = {}
        self.connections: Dict[FrozenSet[str], int] = {}
        self.unique_coords: Set[Tuple[int, int]] = set()

    def parsing(self) -> Optional[Parsed_Map]:
        """
        Parses the configuration file line by line with strict validation.

        Returns:
            Optional[Parsed_Map]:
                Validated map object, or None if errors occur.
        """
        nb_drones_flag: bool = True
        try:
            with open(self.filename, 'r') as file:
                for index, raw_line in enumerate(file, 1):
                    line: str = raw_line.strip()

                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("nb_drones"):
                        if not nb_drones_flag:
                            raise ValueError(
                                f"Line {index}: nb_drones is not first line"
                            )
                        else:
                            self.parse_nb_drones(line, index)
                            nb_drones_flag = False
                        continue
                    elif line.startswith(("start_hub", "end_hub", "hub")):
                        self.parse_hub(line, index)
                    elif line.startswith("connection"):
                        self.parse_connection(line, index)
                    else:
                        raise ValueError(
                            f"Line {index}: unknown instruction"
                        )
                    nb_drones_flag = False
            if self.start is None or self.end is None:
                raise ValueError("Map is missing either start_hub or end_hub")

            return Parsed_Map(
                self.drones_number,
                self.start,
                self.end,
                self.zones,
                self.connections
            )
        except Exception as e:
            print(f"[ERROR] {e}")
            return None

    def parse_nb_drones(self, line: str, index: int) -> None:
        """
        Parses and validates the initial drone count statement.

        Args:
            line (str): The raw instruction line string.
            index (int): Line number location in the input file.
        """
        if ":" not in line:
            raise ValueError(f"Line {index}: Wrong format")
        name, value = [x.strip() for x in line.split(":", 1)]
        try:
            self.drones_number = int(value)
        except ValueError:
            raise ValueError(f"Line {index}: 'nb_drones' must be integer")
        if self.drones_number <= 0:
            raise ValueError(f"Line {index}: 'nb_drones' must be > 0")

    def parse_hub(self, line: str, index: int) -> None:
        """
        Parses hubs and zones metadata, names, and spatial coordinates.

        Args:
            line (str): The raw instruction line string.
            index (int): Line number location in the input file.
        """
        if ":" not in line:
            raise ValueError(
                f"Line {index}: Wrong hub format, missing ':'"
            )
        _type, content = [x.strip() for x in line.split(":", 1)]
        if _type not in ["start_hub", "end_hub", "hub"]:
            raise ValueError(f"Line {index}: wrong hub/zone format!")
        metadata: Dict[str, Any] = {}
        main = None
        meta = None
        if "[" in content:
            if not content.endswith("]"):
                raise ValueError(f"Line {index}: invalid metadata format")
            main, meta = content.split('[', 1)
            metadata = self.parse_metadata("[" + meta, index)
        else:
            main = content
        parts = main.split()
        if len(parts) != 3:
            raise ValueError(f"line {index}: invalid hub format")
        name, x, y = parts
        if any(c in name for c in " -"):
            raise ValueError(
                f"Line {index}: name of the zone contains dash or space"
            )
        try:
            x_int, y_int = int(x), int(y)
        except ValueError:
            raise ValueError(f"Line {index}: coordinates must be intergers")
        current_coord: Tuple[int, int] = (x_int, y_int)
        if current_coord in self.unique_coords:
            raise ValueError(f"Line {index}: duplicate coords")
        self.unique_coords.add(current_coord)
        if _type == "start_hub":
            if self.start is not None:
                raise ValueError("Multiple start_hub definitions")
            self.start = name
        elif _type == "end_hub":
            if self.end is not None:
                raise ValueError("Multiple end_hub definitions")
            self.end = name
        if name in self.zones:
            raise ValueError(f"Line {index}: duplicate hub name '{name}'")
        self.zones[name] = Zone(name, x_int, y_int, metadata)

    def parse_connection(self, line: str, index: int) -> None:
        """
        Parses and registers link routes and maximum capacities between zones.

        Args:
            line (str): The raw instruction line string.
            index (int): Line number location in the input file.
        """
        if ":" not in line:
            raise ValueError(f"Line {index}: wrong connection format")
        _connection, content = line.split(":", 1)
        _connection = _connection.strip()
        content = content.strip()
        metadata: Dict[str, Any] = {}
        main = None
        meta = None
        if "[" in content:
            if "]" not in content:
                raise ValueError(f"Line {index}: wrong metada format")
            main, meta = content.split("[", 1)
            metadata = self.parse_metadata("[" + meta, index)
            main = main.strip()
        else:
            main = content.strip()
        if "-" not in main:
            raise ValueError(f"Line {index}: invalid connection syntax")
        zone1, zone2 = main.split("-", 1)
        zone1 = zone1.strip()
        zone2 = zone2.strip()
        if zone1 == zone2:
            raise ValueError(
                f"Line {index}: self-loop not allowed"
            )
        if zone1 not in self.zones or zone2 not in self.zones:
            raise ValueError(
                f"line {index}: undefined zone in connection"
            )
        frozen_obj: FrozenSet[str] = frozenset({zone1, zone2})
        if frozen_obj in self.connections:
            raise ValueError(f"Line {index}: duplicate connection")
        capacity: int = metadata.get("max_link_capacity", 1)
        if not isinstance(capacity, int):
            raise ValueError(
                f"Line {index}: max_link_capacity must be int"
            )
        if capacity <= 0:
            raise ValueError(f"Line {index}: max_link_capacity must be int")
        self.connections[frozen_obj] = capacity

    def parse_metadata(self, line: str, index: int) -> dict:
        """
        Extracts individual configuration attributes inside bracket groups.

        Args:
            line (str): String snippet enclosing the bracket configurations.
            index (int): Line number location in the input file.

        Returns:
            dict: Evaluated map metadata bindings.
        """
        allowed_keys: Set[str] = {
            "zone", "color", "max_drones", "max_link_capacity"
        }
        allowed_zone_types: Set[str] = {
            "normal", "blocked", "priority", "restricted"
        }
        metadata: Dict[str, Any] = {}
        data_line = line.strip("[]").split()
        for item in data_line:
            if "=" not in item:
                raise ValueError(f"Line {index}: wrong metadata format")
            key, value = item.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key not in allowed_keys:
                raise ValueError(
                    f"Line {index}: unknown metadata key '{key}'"
                )
            if key == "zone":
                if value not in allowed_zone_types:
                    raise ValueError(
                        f"Line {index}: unknown zone type '{value}'"
                    )
            if key == "color":
                if not value.isalpha():
                    raise ValueError(
                        f"Line {index} color hub should be a string"
                    )
            if key == "max_drones":
                try:
                    value_int = int(value)
                except ValueError:
                    raise ValueError(
                        f"Line {index}: max_drones has to be an int"
                    )
                if value_int <= 0:
                    raise ValueError(
                        f"Line {index}: max_drones has to be > 0"
                    )
                metadata[key] = value_int
                continue
            if key == "max_link_capacity":
                try:
                    value_int = int(value)
                except ValueError:
                    raise ValueError(
                        f"Line {index}: max_link_capacity must be int"
                    )
                if value_int <= 0:
                    raise ValueError(
                        f"Line {index}: max_link_capacity must be > 0"
                    )
                metadata[key] = value_int
                continue
            metadata[key] = value
        return metadata
