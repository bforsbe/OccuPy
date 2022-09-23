import os
import numpy as np
import mrcfile as mf
from pathlib import Path
try:
    import map_tools, occupancy, vis, solvent, extras, args              # for pyCharm
except:
    from occupy import map_tools, occupancy, vis, solvent, extras, args   # for terminal use
from skimage.exposure import match_histograms

from typing import Optional
import typer


if __name__ == '__main__':
    typer.run(parse)


def app():
    typer.run(parse)
