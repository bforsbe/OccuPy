# Getting it working

## OccuPy wasn't found

### I used PIP
We recommend installing OccuPy through PIP. This should make `occupy` and `occupy_gui` available as command-line 
tools that you can also assign desktop shortcuts to. However, pip may install occupy in a 
location that is not universally known to your system. In this case you simply have to find where pip installed 
occupy. You can then either make a shortcut to it, and/or add this path to the list of locations your computer looks 
for programs to make the commad-line tools available anywhere on your system.

=== "On Windows"

    1. Find the directory where pip installed OccuPy. In the main menu search bar, type "occupy_gui". You should 
    find an application of the type "Run_command". Click "open file location".

    2. The folder that the file explorer has opened is what you need. Right-click the file "occupy_gui.exe" and 
    click "properties". Right-click the path under "Location" and select all. Copy the path. 
    
    3. Edit the system environment variable "Path" by adding the directory from step 2, e.g. 
    ```C:\Users\IEUser\AppData\Local\Programs\Python\Python310\Scripts```

    4. Optionally, create a shortcut to "occupy_gui.exe".  

=== "On Linux (ubuntu)"
    
    1. In a terminal where pip is avaialble, call ```pip show occupy```. The reported location is a good indication 
    of where occupy was installed. If the locaton is ```/home/bjornf/.local/lib/python3.8/site-packages```, then the 
    location of the program is likely ```/home/bjornf/.local/bin```

    2. To add the path of the program permanently, open the startup list of environment variables. On Ubuntu this is 
    likely /etc/environment. You will need root access for this.

    3. The PATH variable is a colon-separated list. Add the ```occupy_gui``` path as new entry in this list.

    4. If you do mot have the access rights to to this system-wide, you can add the following to your session 
    startup file: ```export PATH=$PATH:</path/to/occupy/program>```