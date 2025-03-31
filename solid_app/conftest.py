import sys
import os
from pathlib import Path

pyproject_root = Path(__file__).parent
sys.path.insert(0, str(pyproject_root))

src_path = os.path.join(pyproject_root, "src")
sys.path.insert(0, src_path)
