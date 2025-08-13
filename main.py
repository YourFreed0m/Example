import argparse
import sys


def run_headless_validation() -> int:
    # Minimal import to avoid creating a window
    from game.textures import ensure_textures_and_atlas
    from game.world import World

    atlas, uvs = ensure_textures_and_atlas()
    world = World(seed=1337)
    world.uvs = uvs
    # Build a few chunks around origin
    for cx in range(-1, 2):
        for cz in range(-1, 2):
            ch = world.ensure_chunk((cx, cz))
            ch.rebuild_mesh(uvs)
    print("Headless validation OK: chunks built and textures ready.")
    return 0


def run_windowed() -> int:
    from game.window import GameWindow
    window = GameWindow(width=1280, height=720, caption="PyCraft")
    window.run()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    try:
        if args.headless:
            sys.exit(run_headless_validation())
        else:
            sys.exit(run_windowed())
    except Exception as exc:
        print(f"Fatal error: {exc}")
        sys.exit(1)