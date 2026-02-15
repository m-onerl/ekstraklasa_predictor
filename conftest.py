import sys
from pathlib import Path

# Add the parent of the project root to sys.path so that the project root
# is treated as a package ("ekstraklasa_predictor"), enabling relative imports
# like `from ..src.scraper...` from within tests/.
project_root = str(Path(__file__).resolve().parent)
parent_dir = str(Path(__file__).resolve().parent.parent)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Remove project root itself so "tests" isn't found as a top-level package
while project_root in sys.path:
    sys.path.remove(project_root)
