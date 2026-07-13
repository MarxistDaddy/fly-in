from typing import Any, Optional


class Zone:
    """
    Represents a map zone node with specific capacities and entry constraints.

    Args:
        name (str): Unique name identifier of the zone.
        x (int): Spatial X-coordinate on the map layout.
        y (int): Spatial Y-coordinate on the map layout.
        metadata (Optional[dict[str, Any]]):
            Optional configurations for type,
            capacity, and color.
    """
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Initializes zone attributes and parses terrain rules from metadata.
        """
        self.name: str = name
        self.x: int = x
        self.y: int = y
        safe_meta = metadata if metadata is not None else {}
        self.zone_type: str = safe_meta.get("zone", "normal")
        self.color: Optional[str] = safe_meta.get("color")
        self.max_drones: int = safe_meta.get("max_drones", 1)
        self.turn_cost: int = self._find_turn_cost_()

    def _find_turn_cost_(self) -> int:
        """
        Determines the required simulation turns to enter this zone type.

        Returns:
            int: Number of turns consumed upon entry (1, 2, or 0 if blocked).
        """
        if self.zone_type == "restricted":
            return 2
        if self.zone_type == "normal" or self.zone_type == "priority":
            return 1
        return 0
