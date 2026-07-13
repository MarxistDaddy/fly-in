import pyglet
from pyglet import shapes
from ParsedMap import Parsed_Map
from typing import Dict, List, Tuple


class Visualizer(pyglet.window.Window):
    """
    Manages the window, map element rendering, and animation playback cycles.

    Args:
        Parsed_Map (Parsed_Map):
            The parsed configuration data containing map geometry.
        simulation_result (Dict[int, List[str]]):
            Calculated turn paths mapped by drone IDs.
    """
    def __init__(
        self,
        Parsed_Map: Parsed_Map,
        simulation_result: Dict[int, List[str]]
    ) -> None:
        """
        Initializes assets, labels, scale mappings,
        and schedules animation ticks.
        """
        self.bg_image = pyglet.image.load("assets/im5.jpeg")
        image_w = self.bg_image.width
        image_h = self.bg_image.height
        self.bird_image = pyglet.image.load("assets/albatross.png")
        self.bird_image.anchor_x = self.bird_image.width // 2
        self.bird_image.anchor_y = self.bird_image.height // 2
        super().__init__(image_w, image_h, caption="Fly-in")
        self.map = Parsed_Map
        self.result = simulation_result
        self.bg_sprite = pyglet.sprite.Sprite(img=self.bg_image)
        self.coord_scale = 75
        self.offset_x = 50
        self.offset_y = 700
        self.render_nodes: List[shapes.Circle] = []
        self.render_edges: List[shapes.Line] = []
        self.animation_speed = 1.0
        self.animation_progress = 0.0
        self.current_turn = 0
        self.max_turns = max(
            len(path) - 1 for path in simulation_result.values()
        ) if simulation_result else 0
        self.manual_mode = False
        self.turn_label = pyglet.text.Label(
            text=f"Turn: {self.current_turn} / {self.max_turns} (AUTO)",
            font_name="Arial",
            font_size=18,
            x=20,
            y=self.height - 30,
            color=(255, 255, 255, 255),
        )
        self.drone_shapes: Dict[int, pyglet.sprite.Sprite] = {}
        for drone_key, path in simulation_result.items():
            sprite = pyglet.sprite.Sprite(img=self.bird_image)
            sprite.scale = 0.08
            self.drone_shapes[drone_key] = sprite
        self.setup_map_graphics()
        pyglet.clock.schedule_interval(self.update_timeline, 1 / 60.0)

    def setup_map_graphics(self) -> None:
        """
        Generates line shapes for links and colored circles for zone hubs.
        """
        for link in self.map.connections:
            zone1, zone2 = list(link)
            z1, z2 = self.map.zones[zone1], self.map.zones[zone2]
            x1 = self.offset_x + (z1.x * self.coord_scale)
            y1 = self.offset_y + (z1.y * self.coord_scale)
            x2 = self.offset_x + (z2.x * self.coord_scale)
            y2 = self.offset_y + (z2.y * self.coord_scale)
            line = shapes.Line(
                x1, y1, x2, y2, thickness=4.0, color=(255, 255, 255)
            )
            self.render_edges.append(line)
        for name, zone in self.map.zones.items():
            x = self.offset_x + (zone.x * self.coord_scale)
            y = self.offset_y + (zone.y * self.coord_scale)
            color_map = {
                "green": (46, 204, 113),
                "red": (255, 30, 30),
                "purple": (155, 89, 182),
                "orange": (230, 126, 34),
                "gold": (241, 196, 15),
                "yellow": (241, 196, 15),
                "blue": (41, 128, 185),
                "brown": (153, 76, 0),
                "crimson": (178, 34, 34),
                "maroon": (85, 0, 0),
                "darkred": (139, 0, 0),
                "black": (0, 0, 0)
            }

            zone_color_str = zone.color if zone.color is not None else ""
            color = color_map.get(zone_color_str, (128, 128, 128))
            circle = shapes.Circle(x, y, radius=20, color=color)
            self.render_nodes.append(circle)

    def get_drone_position(
        self,
        path: List[str],
        turn: int,
        progress: float
    ) -> Tuple[float, float]:
        """
        Calculates interpolated screen coordinatesfor a droneover
        a transition.

        Args:
            path (List[str]):
                Drone route sequence including spatial nodes and links.
            turn (int):
                Current baseline simulation turn.
            progress (float):
                Easing fraction [0.0, 1.0] indicating inter-turn timeline.

        Returns:
            Tuple[float, float]:
                Calculated screen dimensions (X, Y) for target sprite.
        """
        turn_history = [path[0]]
        for step in path[1:]:
            if "-" in step:
                turn_history.append(step.split("-")[-1])
            else:
                turn_history.append(step)
        if turn >= len(turn_history) - 1:
            z_obj = self.map.zones[turn_history[-1]]
            return (
                float(self.offset_x + (z_obj.x * self.coord_scale)),
                float(self.offset_y + (z_obj.y * self.coord_scale))
            )
        curr_node = turn_history[turn]
        next_node = turn_history[turn + 1]
        z_curr = self.map.zones[curr_node]
        z_next = self.map.zones[next_node]
        x1 = self.offset_x + (z_curr.x * self.coord_scale)
        y1 = self.offset_y + (z_curr.y * self.coord_scale)
        x2 = self.offset_x + (z_next.x * self.coord_scale)
        y2 = self.offset_y + (z_next.y * self.coord_scale)
        interp_x = x1 + (x2 - x1) * progress
        interp_y = y1 + (y2 - y1) * progress
        return float(interp_x), float(interp_y)

    def update_timeline(self, time_slice: float) -> None:
        """
        Advances animation progress and recalculates bird sprite coordinates.

        Args:
            time_slice (float):
                Elapsed time delta passed from the Pyglet clock hook.
        """
        if not self.manual_mode:
            self.animation_progress += time_slice / self.animation_speed
            if self.animation_progress >= 1.0:
                self.animation_progress = 0.0
                self.current_turn += 1
                if self.current_turn > self.max_turns:
                    self.current_turn = self.max_turns
        else:
            self.animation_progress = 0.0
        mode_str = "MANUAL" if self.manual_mode else "AUTO"
        self.turn_label.text = (
            f"Turn: {self.current_turn} / {self.max_turns} ({mode_str})"
        )
        for drone_key, path in self.result.items():
            dx, dy = self.get_drone_position(
                path, self.current_turn, self.animation_progress
            )
            self.drone_shapes[drone_key].x = dx
            self.drone_shapes[drone_key].y = dy

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """
        Captures keyboard inputs to jump timelines or toggle states.

        Args:
            symbol (int):
                Pressed keyboard integer code identifier.
            modifiers (int):
                Active modifier flags combination mask (e.g., Shift, Ctrl).
        """
        from pyglet.window import key

        if symbol == key.SPACE:
            self.manual_mode = not self.manual_mode
            self.animation_progress = 0.0
            print(
                "Playback state toggled manually to: "
                f"{self.manual_mode}"
            )

        elif symbol == key.RIGHT:
            self.manual_mode = True
            if self.current_turn < self.max_turns:
                self.current_turn += 1

        elif symbol == key.LEFT:
            self.manual_mode = True
            if self.current_turn > 0:
                self.current_turn -= 1

    def on_draw(self) -> None:
        """
        Clears frame context buffer and issues render orders for
        background and sprites.
        """
        self.clear()
        self.bg_sprite.draw()
        for edge in self.render_edges:
            edge.draw()
        for node in self.render_nodes:
            node.draw()
        for bird in self.drone_shapes.values():
            bird.draw()
        self.turn_label.draw()
