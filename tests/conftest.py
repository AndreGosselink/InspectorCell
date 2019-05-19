from pathlib import Path
import sys

modpath = Path('src').absolute().resolve()
sys.path.insert(0, str(modpath))  
