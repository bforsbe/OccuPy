# OccuPy

A fast and simple python module and program to estimate local scaling of cryo-EM maps, to approximate relative
occupancy and/or resolution, and optionally also equalise the map according to occupancy while suppressing solvent 
amplification.

**Further documentation, instructions, and tutorials are available** [here](https://occupy.readthedocs.io/). 

# Quick install instructions via pip 

Follow the link above for more instrucions. The instructions below are minimal just intended to provide obvious and 
minimal instructions for posterity and development use.

## install from PyPi (pip install)
```shell
pip install occupy
```


## Install from source  (pip install)

If you are a developer or prefer to download the [source code](https://github.com/bforsbe/OccuPy) for some other reason, you can also install from 
the cloned repo

```shell
$ git clone https://github.com/bforsbe/OccuPy.git
$ cd occupy 
$ pip install -e . 
```

You should also be able to simply run the `occupy_lib/occupy_gui.py` to run the GUI or `occupy_lib/occupy.py` for 
the command-line interface. 