class Drone:
    """Represents a drone navigating through the zone network.

    Args:
        drone_id (int): Unique identifier for the drone.
    """
    def __init__(self, drone_id: int):
        """Initializes a drone instance with an identifier and an empty path.
        """
        self.id: int = drone_id
        self.path: list[str] = []
