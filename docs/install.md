# Installation


## Compiled binaries

The GUI is distributed as precompiled binares that you can download and use. You just need to download and 
double-click the executable, and the OccuPy GUI should appear.

The current version is 0.1.7 (alpha)
<p float="left">
<a href="https://drive.google.com/uc?export=download&id=1XZnk8YotHD0CO4LhEZK0_85xecG7Y2ps">
    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Tux.svg/800px-Tux.svg.png" 
    style="width:64px;" hspace="32" Title="Download for linux"></a>

<a href="https://drive.google.com/uc?export=download&id=TBD">
    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Apple_Computer_Logo_rainbow.svg/800px-Apple_Computer_Logo_rainbow.svg.png" 
    style="width:64px;" hspace="32" Title="Download for mac"></a>

<a href="https://drive.google.com/uc?export=download&id=1XZnk8YotHD0CO4LhEZK0_85xecG7Y2ps">
    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Windows_Logo_%281992-2001%29.svg/1280px-Windows_Logo_%281992-2001%29.svg.png" 
    style="width:80px;" hspace="32" Title="Download for windows"></a>

</p>

Previous versions are **not** available as binaries, but only though [PIP](https://pypi.org/project/OccuPy/) and [github](https://github.com/bforsbe/OccuPy).

---

## Using PIP     
Regardless if you are using conda or not, OccuPy can be installed from the [Python Package Index](https://pypi.
org/project/OccuPy/) (PyPI) using `pip`. 

```shell
pip install occupy
```

You can also easily install previous [versions](https://pypi.org/project/OccuPy/#history) using pip: 
```shell
pip install occupy==0.1.6
```

---

## From source 
If you are a developer or prefer to download the [source code](https://github.com/bforsbe/OccuPy) for some other reason, you can also install from 
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
OccuPy is also a command-line tool, so that you can easily script its use if needed for bulk processing. This is 
only available by installing using PIP, or from sourc code. 

We recommend getting acquainted with OccuPy through the GUI, which also has an option to print the command it will run, 
which can then be called on the command-line.  

```shell
$ occupy --version
OccuPy: 0.1.5rc4.dev1+gfa0f2e9.d20220905
```

### The python module
For development use, you can also import it as a python module, but this currently and unsupported  feature that we 
will not prioritize as main functionality.

## Problems 