# Installation

## I'd like to install with pip but I don't know how
To help us make the installation instructions better and help you use python and pip, you can request help 
<a href="https://form.jotform.com/223012138013033" target="_blank" rel="noopener noreferrer">here</a>. 
Please try to complete the installation by the instructions
provided in the install section first, and see if the below can resolve any issues. 

## I installed through pip but OccuPy isn't found
Let's first confirm that it was.
=== "On Windows"

    1. In the main menu search bar, type "powershell", and open a text-based interface to your system. 
    2. Type `py -m pip show occupy` and hit enter. If you see details regarding occupy, then we're good. If not, try 
    writing out "python" instan of just "py": `python -m pip show occupy`. 
    3. If you still don't see details like version and location, then occupy probably wasn't installed properly.
    You need to try to install it according to the install procedures, 
    and <a href="https://form.jotform.com/223012138013033" target="_blank" rel="noopener noreferrer">ask for help</a>
    if you still can't make it work. 

=== "On Linux (ubuntu)"
    
    Open a terminal and type `pip show occupy`, and hit enter. If you don't see details like 
    version and location, then occupy probably wasn't installed properly. If you used a virtual environment when 
    installing, make sure to activate it like you did before, and try again.

If OccuPy you managed to confirm that OccuPy was installed, Pip may have installed OccuPy in a location that is 
not universally known to your system.
You can either tell your system where to look when searching for installed applications, or 
create a shortcut to it that you can find easily. 
In either case, we need to find where occupy was installed.

=== "On Windows"

    1. In a powershell like you just used to verify the install, type 
    `Get-ChildItem $($ENV:userprofile)  -force -Recurse -ErrorAction SilentlyContinue occupy_gui.exe`
    Note the reported directory. 

    2. Open a file browser and enable hidden files under "view".

    3. Browse to the directory where `occupy_gui.exe` was found. 

    4. Option 1: Create a shortcut. Right-click occupy_gui.exe and click "create shortcut". Move the new shortcut to 
    e.g. the desktop.  
    
    5. Option 2: Make sure the occupy directory is included in the paths where the system looks for programs. Edit the 
    system and/or user environment variable "Path" by adding the directory from step 2, e.g. 
    ```C:\Users\IEUser\AppData\Local\Programs\Python\Python310\Scripts```

=== "On Linux (ubuntu)"
    
    1. In a terminal where pip is avaialble, call ```pip show occupy```. The reported location is a good indication 
    of where occupy was installed. If the locaton is ```/home/bjornf/.local/lib/python3.8/site-packages```, then the 
    location of the program is likely ```/home/bjornf/.local/bin```

    2. To add the path of the program permanently, open the startup list of environment variables. On Ubuntu this is 
    likely /etc/environment. You will need root access for this.

    3. The PATH variable is a colon-separated list. Add the ```occupy_gui``` path as new entry in this list.

    4. If you do mot have the access rights to to this system-wide, you can add the following to your session 
    startup file: ```export PATH=$PATH:</path/to/occupy/program>```