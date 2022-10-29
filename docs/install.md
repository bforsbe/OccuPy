

# Installation


## Compiled binaries

The GUI is distributed as precompiled binares that you can download and use. You just need to download and 
double-click the executable, and the OccuPy GUI should appear.

Version :fontawesome-solid-tag: 0.1.7 (alpha)


<div class="grid" markdown>
<span style="font-size:1.5em;">
&nbsp;&nbsp;:fontawesome-brands-linux:&nbsp;&nbsp;
<a href="https://drive.google.com/uc?export=download&id=1XZnk8YotHD0CO4LhEZK0_85xecG7Y2ps" title="Compiled binary 
for Linux">
 __Linux__ OccuPy GUI </a></span>
{ .card }


<span style="font-size:1.5em;">
&nbsp;&nbsp;:fontawesome-brands-apple:&nbsp;&nbsp;
<a href="https://drive.google.com/uc?export=download&id=TBD" title="Compiled binary 
for Linux">
 __Apple__ OccuPy GUI </a></span>
{ .card }

<span style="font-size:1.5em;">
&nbsp;&nbsp;:fontawesome-brands-windows:&nbsp;&nbsp;
<a href="https://drive.google.com/uc?export=download&id=TBD" title="Compiled binary 
for Linux">
 __Windows__ OccuPy GUI </a></span>
{ .card }


</div>

[//]: # ()
[//]: # (<p float="left">)

[//]: # (<a href="https://drive.google.com/uc?export=download&id=1XZnk8YotHD0CO4LhEZK0_85xecG7Y2ps">)

[//]: # (    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Tux.svg/800px-Tux.svg.png" )

[//]: # (    style="width:64px;" hspace="32" Title="Download for linux"></a>)

[//]: # ()
[//]: # (<a href="https://drive.google.com/uc?export=download&id=TBD">)

[//]: # (    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Apple_Computer_Logo_rainbow.svg/800px-Apple_Computer_Logo_rainbow.svg.png" )

[//]: # (    style="width:64px;" hspace="32" Title="Download for mac"></a>)

[//]: # ()
[//]: # (<a href="https://drive.google.com/uc?export=download&id=1XZnk8YotHD0CO4LhEZK0_85xecG7Y2ps">)

[//]: # (    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Windows_Logo_%281992-2001%29.svg/1280px-Windows_Logo_%281992-2001%29.svg.png" )

[//]: # (    style="width:80px;" hspace="32" Title="Download for windows"></a>)

[//]: # ()
[//]: # (</p>)

Previous versions are **not** available as binaries, but only though [PIP](https://pypi.org/project/OccuPy/) and 
[github](https://github.com/bforsbe/OccuPy). The same goes for the command-line tool. Istallation through PIP is 
described below. 

---

## Using PIP     
Regardless if you are using conda or not, OccuPy can be installed from the [Python Package Index](https://pypi.
org/project/OccuPy/) (PyPI) using `pip`. 

### Verify/install python and/or pip
=== "Windows"

    The following contains elements of
    [this](https://www.digitalocean.com/community/tutorials/install-python-windows-10) guide to installing python on 
    windows, and 
    [this](https://pip.pypa.io/en/stable/installation/#get-pip-py) guide to install pip using python. 
    
    1. In the start-menu, type "Powershell". Open a powershell terminal.
    2. Check if python is installed by calling `python --version` in the powershell. If you see a version number, 
    python is installed. If not, install python by visiting [python.org](https://www.python.org/downloads) and select 
    the windows installer. Follow the instructions, and refer to 
    [this](https://www.digitalocean.com/community/tutorials/install-python-windows-10) guide if needed. 
    Close the powershell and reopen it once python is installed. 
    3. Check if pip is installed by calling `pip --version` in the powershell. If you see a version number, pip 
    is installed, and you can skip to step 5. If not, download the file `get-pip.py` from 
    [pypa.io](https://bootstrap.pypa.io). Put it in the same folder as the powershell is running. You can find out 
    where the powershell is running, by calling `pwd` in it.
    4. In the powershell, run the downloaded file by calling `python get-pip.py` and hit enter. This will install pip. 
    5. You may need to add pip to your environment variables, as described in 
    [this guide](https://www.activestate.com/resources/quick-reads/how-to-install-pip-on-windows/).

=== "Linux (ubuntu)"

    Please follow [this guide](https://tecadmin.net/how-to-install-python-3-10-on-ubuntu-debian-linuxmint/),
    which also explains and verifies that pip is installed along with python.

### Install OccuPy

=== "Windows"
    
    1. In the start-menu, type "Powershell". Open a powershell terminal.
    2. In the powershell, call `pip install occupy`.
    **Take note** of any notice about where OccuPy and it's dependencies were installed, and if it was suggested that 
    you add this to your path. Please add the path to your environment variables if asked, as described in 
    [this guide](https://www.activestate.com/resources/quick-reads/how-to-install-pip-on-windows/).
    3. Verify the install by calling `pip show occupy`. You will either see `WARNING: Package(s) not found: occupy` 
    or a description of the installation. If successfully installed, continue. 
    4. In the powershell, call "occupy_gui". If you get an error starting with 
    `occupy_gui : The term 'occupy_gui' is not recognized...`
    then you need to add the pip path as described in step 2. Otherwise, the occupy GUI should start. 
    5. Note also that calling `occupy` in the powershell will invoke the non-GUI tool. 
    Call `occupy --help` for a list of input options. 

=== "Linux (ubuntu)"

    1. Open a terminal.
    2. In the terminal, call `pip install occupy`.
    3. Verify the install by calling `pip show occupy`. You will either see `WARNING: Package(s) not found: occupy` 
    or a description of the installation. If successfully installed, continue. 
    4. In the powershell, call "occupy_gui". If you get the error 
    `command not found: occupy_gui`
    then you need to add the pip path to your environment variables, or restart the terminal. Otherwise, the occupy GUI 
    should start. 
    5. Note also that calling `occupy` in the terminal will invoke the non-GUI tool. 
    Call `occupy --help` for a list of input options.

<div class="admonition Hint">
<p class="admonition-title">Update, or downgrade easily</p>
<p>
You can also easily install previous <a href="https://pypi.org/project/OccuPy/#history">versions</a> using pip: 

```shell
pip install occupy==0.1.6
```
</p>
</div>


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

