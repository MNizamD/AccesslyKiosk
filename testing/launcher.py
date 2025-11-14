from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
import sys

def import_external(module_path: Path):
    sys.path.insert(0, str(module_path.parent))  # <── add containing folder
    spec = spec_from_file_location(str(module_path.name), module_path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(f"{module_path} not found.")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

if __name__ == "__main__":
    APP_DIR = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(sys.argv[0]).parent
    app = import_external(APP_DIR / "web_wall" / "app.py")
    app.run(APP_DIR / "web_wall")