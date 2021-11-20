import argparse
import shutil
from pathlib import Path
from importlib import import_module
import os

from solid import scad_render_to_file


def main(args):
    if args.github:
        print("We are running on GitHub Actions")
    print("Cleaning export folder")
    try:
        shutil.rmtree("export")
    except FileNotFoundError:
        pass
    os.makedirs("export")
    for root, _, files in os.walk("."):
        for f in files:
            path = Path(root) / f
            if path.suffix == ".py" and path.stem != "export":
                module = ".".join(path.with_suffix("").parts)
                print(f"Importing {module}")
                mod = import_module(module)
                if hasattr(mod, "assembly"):
                    assemblies = [mod.assembly()]
                elif hasattr(mod, "assemblies"):
                    assemblies = mod.assemblies()
                else:
                    print(f"Warning: no assemblies found in {module}")
                    continue

                if (
                        hasattr(mod, "GH_ACTIONS_DISABLE")
                        and mod.GH_ACTIONS_DISABLE
                        and args.github):
                    print(
                        f"Warning: export of {module} is disabled on "
                        "GitHub Actions"
                    )
                    continue
                for idx, a in enumerate(assemblies):
                    export_path = (
                        Path("export")
                        / f"{module}_{idx}.scad"
                    )
                    file_out = scad_render_to_file(a, export_path)
                    print(f"Exported {file_out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--github', action='store_true')
    args = parser.parse_args()
    main(args)
