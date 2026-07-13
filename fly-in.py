import sys
from parsing import Parser
from graph import Graph
from visualizer import Visualizer


def main() -> None:
    """
    Orchestrates map parsing, pathfinding execution, and visual playback.

    Args:
        None (Reads config file path from sys.argv).

    Returns:
        None

    Raises:
        SystemExit: If arguments are invalid,
        parsing fails, or execution errors.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 fly-in.py config.text")
        sys.exit(1)
    parser = Parser(sys.argv[1])
    parsed_data = parser.parsing()
    if not parsed_data:
        sys.exit(1)
    graph = Graph(parsed_data)
    result = {}
    try:
        result = graph.run_all_drones()
    except Exception:
        sys.exit(1)
    if result:
        max_steps = max(len(path) for path in result.values()) - 1
        for step in range(1, max_steps + 1):
            turn_output = []
            for drone_key, path in result.items():
                if step >= len(path):
                    continue
                prev_pos = path[step - 1]
                curr_pos = path[step]
                if curr_pos != prev_pos:
                    turn_output.append(f"D{drone_key}-{curr_pos}")
            if turn_output:
                print(" ".join(turn_output))
    import pyglet
    Visualizer(parsed_data, result)
    pyglet.app.run()


if __name__ == "__main__":
    main()
