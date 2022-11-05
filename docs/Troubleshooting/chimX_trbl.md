# ChimeraX 

## ChimeraX was not found 
If the "Launch ChimeraX" button indicates "(not found)", then OccuPy has not found chimeraX.

OccuPy looks for chimeraX every time it starts, by looking for a program that can be run by executing `chimerax` in 
a terminal. It also looks for some alternate spellings. If you have ChimeraX in your path, it should be found. If 
not, you have to add the chimeraX program-file to the path.


=== "On Windows"

    1. Find the directory where the chimeraX program-file has been installed on your system. One way is to check the 
    properties of your chimeraX-shortcut.
    2. Edit the system environment variable "Path" by adding the directory from step one, e.g. 
    ```C:\Program Files\ChimeraX\bin```
    3. Restart OccuPy to see if chimeraX was detected.

=== "On Linux (ubuntu)"

    1. Find the directory where chimerax is installed on your system. One way is to start chimeraX and open a terminal. 
    in the terminal, type and execute
      ```commandline
      $ ps aux | grep chimerax
      bjornf    248767 13.9  1.2 4027076 206084 ?      Sl   16:30   0:04 /usr/bin/chimerax -- ...
      ```
    Which indicates that `/usr/bin/chimerax` is the location of the chimerax program file.
    2. To add an environment variable permanently, open the startup list of environment variables. On Ubuntu this is 
    likely /etc/environment. You will need root access for this.
    3. Add a new line: 
    `OCCUPY_CHIMERAX = <path from step 1>/chimerax` 
    Save the file. 
    4. Restart OccuPy to see if chimeraX was detected.

## There's a big "X" covering the map

<div class="admonition danger">
<p class="admonition-title">This could be bad</p>
<p>
This is an explicit warning. OccuPy estimates a solvent model, but also recognizes when this solvent model is a poor 
fit. In that case, OccuPy makes sure that you notice. 
</p>
</div>

### This warning is ok to ignore if...

1. **If you are just estimating relative resolution**, then the solvent model and confidence are not used. You can 
   then safely ignore the warning and hide it from view in the chimeraX model list. 

2. If you are estimating occupancies **without modification**, then the solvent model and confidence are not used. You can 
   then safely ignore the warning and hide it from view in the chimeraX model list.

### You need to fix the situation if...

**If you intend to modify the map** based on the estimated occupancy, or use the confidence map for anything, this 
warning is very serious. A bad solvent model leads to low confidence. OccuPy does not permit modification with low 
confidence over solvent, because it aims to avoid amplifying "false" things within solvent. 
<br><br>
Please consult the <a href="../Tutorials/case/modification">tutorial on map modification</a> to fix the situation.  





