# GUI overview


The GUI of OccuPy allows you to open maps and view them as sliced 2D images. OccuPy is not meant to visualize the 
map in any great detail, this is for you to make appropriate consistency checks. For fine analysis, the GUI will 
call out to open ChimeraX, a much more sophisticated visualization tool.

The GUI automatically calculates and adjusts kernel settings per the users direction, and permits interactive 
evaluation of map modification. 

The GUI also exposes tools to generate maks based on the estimated scale.

![image](https://drive.google.com/uc?export=view&id=10KrTBE-MLiQ4wu7kfjIKcupYLvydnxxu)

---

## Input map
The map to be used as input. When you run OccuPy through the GUI it will the currently selected map. 
OccuPy supports cubic .map and .mrc files. Occasionally, .ccp4 files cause issues. 

<div class="admonition attention">
<p class="admonition-title">OccuPy wants raw input</p>
<p>
OccuPy was designed to expect unsharpened maps with solvent noise, so it's best to not 
mask or post-process your map. In most cases its fine to do this too, but it's not recommended.
</p>
</div>

<div class="admonition error">
<p class="admonition-title">AI maps try too hard</p>
<p>
Machine-learning tools for post-processing alter the map in ways that OccuPy was not designed to anticipate. If 
you provide a 
map that has been altered by machine-learning methods, the output should be considered vey unreliable.
</p>
</div>

There is also an "emdb" button to fetch and unzip the main map of any EMD entry. 

---

## Scale Kernel Settings
When you provide an input map, OccuPy checks the box dimensions and voxel size. Based on this, it calculates 
suggested parameters to estimate the local scale with accuracy and confidence. 

If you change these parameters, parameters below may be updated. Changing some of these parameters will alter the 
local scale estimate, so leave them unchanged until you have gone through one of the specific tutorials and 
understand what they do. 

<div class="admonition hint">
<p class="admonition-title">Details depend on use</p>
<p>
More detailed specification of the scale kernel settings are described in the tuorials that describe estimation of 
occupanvy and relative resolution, since they influence each case slightly differently. 
</p>
</div>

---

## Modification options
In some cases you may want to change the input map based on the scale estimate. This is where you do that. 
<br><br>
If the scale you have selected (below the viewer) is in "occupancy" mode (name has 'occ' in it), OccuPy will
let you use it to modify. The active modification will be interactively approximated in the "preview" and "plot"
tab of the viewer.
<br><br>
If the scale you have selected (below the viewer) is in "resolution" mode (name has 'res' in it), OccuPy will *not* 
let you use it to modify, which will inactivate the "preview" tab of the viewer and the "Modify Map" button.  
<div class="admonition hint">
<p class="admonition-title">It's easier done than said</p>
<p>
If you try it out and follow one or more tutorials, this will make more sense than any explanation. More detailed 
specification of the modification options are e.g. described in the tutorial on map modification.
</p>
</div>

---

## Optional/extra 
These are options that you would normally not use, but that you might want to play with in certain cases. You can 
skip this section for now, leaving them at default values.
### Limit box size 
OccuPy down-samples the input map to this size for all internal calculations, using a Fourier-crop (low-pass) 
procedure. This makes OccuPy use less memory and run faster. Any modified output is zero-padded in Fourier space to 
match the input dimension. 
### Ouput lowpass 
This is only relevant for modified output. Beyond the limited box-size described above, OccuPy applies any 
modification on the full-resolution input, not the low-passed input. So if the output should be low-passed, this 
must be specified. 
### Naive normalization
This is an option to ignore the tile size specified in the kernel settings. In this case, the scale estimation 
becomes very sensitive to the Tau percentile (also a kernel setting), which might be desirable in some very special 
circumstances. 
### Histogram-match to input
Histogram-matching is a procedure to make the greyscale and contrast of two images as equal as possible. In some 
cases this might be desirable to enforce, but most of the time the greyscale of the output will very closely match 
the input anyway. 

---

## The viewer

### Input 
The map currently selected in the "input map" drop-down menu above. 
### Scale
The map currently selected in the "scale map" drop-down menu **below** the viewer. You can either add files to this 
drop-down 
by browsing or by running OccuPy. 
### Conf. 
The estimated solvent confidence from the previous time OccuPy was run. This is based on the estimated solvent model,
which can be viewed on the tab adjacent to the output log. The confidence is used to restrict any modification, so 
that solvent isn't amplified or attenuated.
### Sol.def
The map currently selected in the "solvent def" drop-down menu below. The solvent definition restricts the 
estimation of a solvent model. This is not typically required. 
### Preview
If you have an input and occupancy-mode scale selected, this will show a preview of the modification. **This does 
not account for confidence and solvent compensation, and will look worse than the actual output**. 

---

## The output log 
This will document what is happening, for our convenience. But everything is also documented in the full log, which 
you can access either through the menu or by double-clicking the output log *tab*. 

<div class="admonition attention">
<p class="admonition-title">Some clutter during testing</p>
<p>
OccuPy is currently being alpha-tested, so there's a bunch of extra output to make it easier to respond to user 
issues. These lines begin with "AT: " and should be colored green. You can safely ignore them. 
</p>
</div>

---

## The Menu 
Control over where OccuPy writes output, and other conventional options. 




