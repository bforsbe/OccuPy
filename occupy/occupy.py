import os
import numpy as np
import mrcfile as mf
from pathlib import Path
try:
    import estimate, args              # for pyCharm
except:
    from occupy import estimate, args   # for terminal use
from skimage.exposure import match_histograms

from typing import Optional
import typer


if __name__ == '__main__':
    options = typer.run(args.parse)
    estimate.occupy_run(options)


def app():
    options = typer.run(args.parse)
    estimate.occupy_run(options)

