# Installation
Regardless if you are using conda or not, OccuPy can be installed from the [Python Package Index](https://pypi.
org/project/OccuPy/) (PyPI) using `pip`

```shell
pip install occupy
```
If you are a developer or prefer to download the source code for some other reason, you can also install from 
the cloned repo

```shell
$ git clone https://github.com/bforsbe/OccuPy.git
$ cd occupy 
$ pip install -e . 
```

---

## Usage
### The GUI
Occupy has a GUI that is recommended to use, because it makes the processing steps more intuitive, presents the 
options plainly, and offer easy ways to check your input and processing results for consistency. 

To **start the GUI** from the command-line (terminal) and it is in your path (e.g. if you used pip install), simply call

```shell
$ occupy_gui
```

If it is not in your path, simply specify its location, or add it to your path.

If you downloaded a binary, simply double-click it.

### The command-line tool
OccuPy is also a command-line tool, so tht you can easily script its use if needed for bulk processing. We still 
recommend getting acquainted through the GUI, which also has an option to print the command it will run, which can 
then be called on the command-line.  

The command-line tool uses typer to manage input options, which has rich syntax highlighting and error reporting.
```shell
$ occupy --version
OccuPy: 0.1.5rc4.dev1+gfa0f2e9.d20220905
```

### The python module
For development use, you can also import it as a python module, but this currently and unsupported  feature that we 
will not prioritize as main functionality.

## Problems 