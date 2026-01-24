# Installation

## The precompiled binary isn't working 

=== "On Windows"

    <br>
    We are not aware of how the installation might have failed on windows. Please submit an 
    <a href="https://github.com/bforsbe/OccuPy/issues">issue</a>, describing your windows version, and 
    any extra observations that might be helpful. 

=== "On Mac"

    1. Note that it can take ~1 min for it to start.
    2. The OccuPy GUI may be recognized as coming from an untrusted or "unidentified developer", and produce a warning 
    message the first time you run the program. **This requires administrator privileges.**
    3. If doulbe-clicking the binary does not open the GUI, right-click on the OccuPy GUI binary file and select 
    "Open", and then click the "Open" button in the window that appears.
    4. If it opens as a text file, you will need to mark the file as an executable. Unfortunately, you need to do this in a 
    terminal as described 
    <a href="https://support.apple.com/en-gb/guide/terminal/apdd100908f-06b3-4e63-8a87-32e71241bab4/mac">here</a>.
    The file icon should now appear to be a small terminal window. Double-clicking the file should open the OccuPy GUI. 
    3. If the above doesn’t work, you can run the binary from the terminal, which may provide some more info.
    Open a terminal in the folder where the OccuPy GUI binary is located, and run it by typing `./occupy_gui`
    4. If you still have not been able to resolve the issue, please look through existing 
    <a href="https://github.com/bforsbe/OccuPy/issues">issues</a>, 
    and submit a new issue/question if you still can't make it work.

=== "On Linux (ubuntu)"

    <br>
    We are not aware of how the installation might have failed on linux. Please submit an 
    <a href="https://github.com/bforsbe/OccuPy/issues">issue</a>, describing your system and observations.

## The GUI window looks too big/small/...

On some (e.g. 4K) screens, the high resolution causes graphical elements to be re-scaled. OccuPy knows about this 
and does its best to get it right, but we have not been able to test on a wide range of screen sizes and resolutions.  


=== "On Windows"

    1. Locate the installed occupy.exe program file.  
    2. Right-click the binary file and choose properties. 
    3. Under "Compatability", Click "Change high DPI settings"
    4. Select "Override high DPI scaling behaviour", and change the setting so that scaling is performed by "system". 
    5. Apply and close.
    6. Restart OccuPy.
    
    If the problem remains unresolved, please <a href="https://github.com/bforsbe/OccuPy/issues">report</a> this to 
    the developers so that we can make sure that it doesn't happen in the future.

=== "On Mac"

    <br>
    We have not had any reports of poor scaling of the GUI on Mac.
    <br>
    <div class="admonition bug">
    <p class="admonition-title">Report any issues</p>
    <p>
    If your GUI does not look like the image in the "GUI overview" tutorial, please 
    <a href="https://github.com/bforsbe/OccuPy/issues">report</a> this to the developers so that we can make sure 
    that it doesn't happen in the future.
    </p>
    </div>

=== "On Linux (ubuntu)"

    <br>
    We have not had any reports of poor scaling of the GUI on Linux systems.
    <br>
    <div class="admonition bug">
    <p class="admonition-title">Report any issues</p>
    <p>
    If your GUI does not look like the image in the "GUI overview" tutorial, please 
    <a href="https://github.com/bforsbe/OccuPy/issues">report</a> this to the developers so that we can make sure 
    that it doesn't happen in the future.
    </p>
    </div>


## I'd like to install with pip but I don't know how
To help us make the installation instructions better and help you use python and pip, you can request help 
<a href="https://form.jotform.com/223012138013033" target="_blank" rel="noopener noreferrer">here</a>. 
Please try to complete the installation by the instructions
provided in the install section first, and see if the below can resolve any issues. 

## I installed through pip but OccuPy isn't found
Let's first confirm that it was in fact installed. 
=== "On Windows"

    1. In the main menu search bar, type "powershell", and open a text-based interface to your system. 
    2. Type `py -m pip show occupy` and hit enter. If you see details regarding occupy, then we're good. If not, try 
    writing out "python" instead of just "py": `python -m pip show occupy`. 
    3. If you still don't see details like version and location, then occupy probably wasn't installed properly.
    You need to try to install it according to the install procedures, 
    and <a href="https://form.jotform.com/223012138013033" target="_blank" rel="noopener noreferrer">ask for help</a>
    if you still can't make it work. 

=== "On Mac"
    
    Open a terminal and type `pip show occupy`, and hit enter. If you don't see details like 
    version and location, then occupy probably wasn't installed properly. If you used a virtual environment when 
    installing, make sure to activate it like you did before, and try again.

=== "On Linux (ubuntu)"
    
    Open a terminal and type `pip show occupy`, and hit enter. If you don't see details like 
    version and location, then occupy probably wasn't installed properly. If you used a virtual environment when 
    installing, make sure to activate it like you did before, and try again.

If you managed to confirm that OccuPy was installed, Pip may have installed OccuPy in a location that is 
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

=== "On Mac"
    
    1. In a terminal where pip is available, call ```pip show occupy```. The reported location is a good indication 
    of where occupy was installed. If the locaton is ```/home/bjornf/.local/lib/python3.8/site-packages```, then the 
    location of the program is likely ```/home/bjornf/.local/bin```

    2. To add the path of the program permanently, open the startup list of environment variables. On Ubuntu this is 
    likely /etc/environment. You will need root access for this.

    3. The PATH variable is a colon-separated list. Add the ```occupy_gui``` path as new entry in this list.

    4. If you do not have the access rights to do this system-wide, you can add the following to your session 
    startup file: ```export PATH=$PATH:</path/to/occupy/program>```

=== "On Linux (ubuntu)"
    
    1. In a terminal where pip is available, call ```pip show occupy```. The reported location is a good indication 
    of where occupy was installed. If the locaton is ```/home/bjornf/.local/lib/python3.8/site-packages```, then the 
    location of the program is likely ```/home/bjornf/.local/bin```

    2. To add the path of the program permanently, open the startup list of environment variables. On Ubuntu this is 
    likely /etc/environment. You will need root access for this.

    3. The PATH variable is a colon-separated list. Add the ```occupy_gui``` path as new entry in this list.

    4. If you do not have the access rights to do this system-wide, you can add the following to your session 
    startup file: ```export PATH=$PATH:</path/to/occupy/program>```
