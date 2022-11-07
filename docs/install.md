

# Installation


## Compiled binaries
<div class="admonition attention">
<p class="admonition-title">Pre-compiled binaries are not up-to-date during alpha/beta-testing</p>
<p>
When software is recently released, it is expected that users report bugs and that these get mended over time. This is 
called (early) alpha-tesing and (later) beta-testing. OccuPy is in alpha.
<br><br>
Compiled binaries will not be updated as new bugfixes get implemented. Once alpha/beta testing is over, new binaries 
will be provided. 
<br><br>
Using pip install, you can get bugfixes at any time, and update according to the latest changes. If you don't want 
to wait for a new release of bug-fixes, install with pip from source, as described below).
</p>
</div>


The GUI will be distributed as precompiled binaries that you can download and use. You just need to download and
double-click the executable, and the OccuPy GUI should appear. Depending on your operating system, you might need to 
"enable" it by adding permissions and assuring that it isn't a virus. Detailed instructions for this can be found in 
the <a href="../Troubleshooting/install_trbl/">troubleshooting section</a>.
<br><br>
Occupy GUI version :fontawesome-solid-tag: 0.1.7 (alpha).
<br><br>
<div class="gallery-dl">

    <div class="dl-box">
    <a class=nocolor href="https://drive.google.com/uc?export=download&id=1j30PKVwX8GpiqKPJQAhU7rAQ3BOGow1k">
    <img src="../gallery/thumbs/mac_thumb.png" alt="" />
      <div class="transparent-box-dl">
        <div class="dl-caption">
          <p> &nbsp;&nbsp;&nbsp;&nbsp;Mac </p>
            <p class="opacity-low">OccuPy GUI</p>
        </div>
      </div> 
    </a>
    </div>

    <div class="dl-box">
    <a class=nocolor href="https://drive.google.com/uc?export=download&id=1El8D0hdCIkwcbVM_LXaRXA9bd9V8sNB6">
    <img src="../gallery/thumbs/win_thumb.png" alt="" />
      <div class="transparent-box-dl">
        <div class="dl-caption">
          <p> Windows </p>
            <p class="opacity-low">OccuPy GUI</p>
        </div>
      </div> 
    </a>
    </div>

    <div class="dl-box">
    <a class=nocolor href="https://drive.google.com/uc?export=download&id=1XZnk8YotHD0CO4LhEZK0_85xecG7Y2ps">
    <img src="../gallery/thumbs/linux_thumb.png" alt="" />
      <div class="transparent-box-dl">
        <div class="dl-caption">
          <p> &nbsp;&nbsp;Linux </p>
            <p class="opacity-low">OccuPy GUI</p>
        </div>
      </div> 
    </a>
    </div>

</div>

<br>
If you have issues using the pre-compiled binaries, please check the 
<a href="../Troubleshooting/install_trbl/">troubleshooting section</a>. 
<br><br>
Previous versions of OccuPy are **not** available as binaries, but only though [PIP](https://pypi.
org/project/OccuPy/) and 
[github](https://github.com/bforsbe/OccuPy). The same goes for the command-line tool. Installation through PIP is 
described below.




---

## Using PIP     
Regardless if you are using conda or not, OccuPy can be installed from the [Python Package Index](https://pypi.
org/project/OccuPy/) (PyPI) using `pip`.  

<div class="admonition attention">
<p class="admonition-title">Stop. Get help.</p>
<p>
If you run into issues, check the <a href="../Troubleshooting/install_trbl/">troubleshooting section</a>. 
</p>
</div>
### Verify/install python and/or pip
=== "Windows"

    The following contains elements of
    [this](https://www.digitalocean.com/community/tutorials/install-python-windows-10) guide to installing python on 
    windows, and 
    [this](https://pip.pypa.io/en/stable/installation/#get-pip-py) guide to install pip using python. 
    
    1. In the start-menu, type "Powershell". Open a powershell, which is a text-based interface to run system commands.
    2. Check if python is installed by running the command `python --version` in the powershell. If you see a version 
    number, python is installed. 
    If not, download and click the python3.10 installer for windows, which you can get thorugh 
    [this link](https://www.python.org/ftp/python/3.10.8/python-3.10.8-amd64.exe). 
    Follow the instructions on screen to install.     
    3. Close the powershell and reopen it once python is installed.
    4. Check if pip is installed by calling `py -m pip --version` in the powershell. If you see a version number, 
    pip is installed, you can go to the next section to install OccuPy. If not, continue with step 5.  
    5. Download the file `get-pip.py` from [pypa.io](https://bootstrap.pypa.io/get-pip.py) by saving it in the 
    "Downloads" folder. 
    6. In the powershell, run the command "cd ~/Downloads". If you now run `ls *.py` you should see the file 
    "get-pip.py" you just downloaded.
    7. In the same powershell, run the downloaded file by running the command `py get-pip.py` and hit enter. This 
    will install pip. 
    8. You may need to add pip to your **environment variables**, as described in the later section of
    [this guide](https://www.activestate.com/resources/quick-reads/how-to-install-pip-on-windows/).

=== "Linux (ubuntu)"

    Please follow [this guide](https://tecadmin.net/how-to-install-python-3-10-on-ubuntu-debian-linuxmint/),
    which also explains and verifies that pip is installed along with python.

### Install OccuPy

=== "Windows"
    
    1. If you do not have on open, start a powershell as in step 1 of the previous section.
    2. In the powershell, run `py -m pip install occupy`.
    3. Verify the install, run `py -m pip show occupy`. 
    <br>You will either see `WARNING: Package(s) not found: occupy` 
    or a description of the installation. If successfully installed, continue. 
    4. In the powershell, call `occupy_gui`. The occupy GUI should start. 
    <br>If instead you get an error starting with 
    `occupy_gui : The term 'occupy_gui' is not recognized...`
    then you need to add the pip package path to your environment variables. 
    <br> To do so, run 
    ```Get-ChildItem  -Recurse -ErrorAction SilentlyContinue -Filter occupy_gui.exe -Force``` in the powershell. 
    This will find the **Directory** where occupy was installed. Copy it.
    <br> Add the location you copied to the "Path" as described in the section "Adding PIP To Windows Environment 
    Variables" of 
    [this guide](https://www.activestate.com/resources/quick-reads/how-to-install-pip-on-windows/#:~:text=Adding%20PIP%20To%20Windows%20Environment%20Variables).
    5. Note also that calling `occupy` in the powershell will invoke the non-GUI tool. 
    <br>Call `occupy --help` for a list of input options. 

=== "Linux (ubuntu)"

    1. Open a terminal.
    2. In the terminal, call `pip install occupy`.
    3. Verify the install by calling `pip show occupy`. You will either see `WARNING: Package(s) not found: occupy` 
    or a description of the installation. If successfully installed, continue. 
    4. In the terminal, call `occupy_gui`. If you get the error 
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

### Make it easy to run without a terminal

=== "Windows"

    In the start menu, type `occupy_gui`. You should find occupy_gui as the type "Run command" suggested. 
    If this is not convenient enough:  

    1. Right-click the occupy_gui run command and choose "open location".
    2. Right-click `occupy_gui.exe` and click "create shortcut". Move the shortcut to e.g. the desktop.

=== "Linux (ubuntu)"
    
    To create a launcher that makes it easy to start occupy, do the following. 
    This is derived from [this guide](https://www.maketecheasier.com/create-desktop-file-linux/)

    1. Open a new text file and give it the following content: 
    ```txt
    [Desktop Entry]
    Type=Application
    Terminal=false
    Exec=/path/to/executable
    Name=OccuPy
    ```
    2. Replace the `Exec` value with the path to occupy. To find it, open a terminal and call `which occupy_gui`.
    3. Save the file as `occupy.desktop` in `/usr/share/applications/`. This may require root access. 

---

## Install from source 
If you are a developer or prefer to download the [source code](https://github.com/bforsbe/OccuPy) for some other reason, you can also install from 
the cloned repo

```shell
git clone https://github.com/bforsbe/OccuPy.git
cd occupy 
pip install -e . 
```
We recommend you do this in a virtual environment. More on this and specific dev use in the final section on this page.

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

## Developer use

### Dev tools
These are instructions to install the developer tools used to build documentation, build binaries, etc. **This is not 
needed to use occupy.**

1. clone the repo 
```shell
git clone https://github.com/bforsbe/OccuPy.git
```
2. make a clean [virtual environment](https://www.dataquest.io/blog/a-complete-guide-to-python-virtual-environments/)
```shell
mkdir occupy/occupy_venv
python3 -m venv ocucpy/occupy_venv
source ocucpy/occupy_venv/bin/activate
```
3. pip install occupy, deps and dev-deps in the virtual environment
```shell
pip install -e occupy/".[dev]"
```

4. build binary 
```shell
cd occupy 
pyinstaller --onefile --windowed occupy_lib/occupy_gui.py 
ls dist 
```

5. build docs and start a local serve to view them (interactive with changes)  
```shell
mkdocs serve 
```

### The python module
For development use, you can also import it as a python module, but this currently and unsupported feature that we 
will not prioritize as main functionality.

```python
In [1]: import occupy_lib
In [2]: from occupy_lib.map_tools import create_radial_mask
In [3]: create_radial_mask?
Signature:
create_radial_mask(
    size: int,
    dim: int,
    center: int = None,
    radius: float = None,
)
Docstring:
Create a circular or spherical dimensional mask or kernel

:param size:    Output array length
:param dim:     Output array dimension
:param center:  Center of the radial region
:param radius:  Radius of the radial region
:return:        Boolean array
File:      ~/Documents/Occ/occupy/occupy_lib/map_tools.py
Type:      function

```


