# Use a solvent definition


<div class="admonition hint">
<p class="admonition-title">Recommendation</p>
<p>
Please read the GUI overview and conduct the intro tutorial first.
</p>
</div>

<div class="admonition attention">
<p class="admonition-title">Be lazy</p>
<p>
The solvent model is only used for map modification and solvent suppression, so if you are not doing any of these, e.
g. if you just need to estimate the scale, you need <strong>not</strong> do this tutorial.
</p>
</div>

In some cases, the solvent peak is not dominant in the input map histogram. Common reasons include

1. over-sharpening of a map to introduce uniform noise that dominates the solvent noise
2. insufficient input lowpass filtering  
3. reconstructions of partial regions like viral capsids, where little to no solvent is included

In these cases, OccuPy can make use of a solvent mask, that instructs it where to look for the solvent peak. However, it
is **not used a mask for the modification or output**. There are benefits to this, like being able to find something 
significant outside your mask and amplifying or attenuating it as well. 

--- 

## 1. Try a higher low-pass value
This is the simple approach, and if it works satisfactorily, use it. 

1. Open the input map and estimate the scale.
2. Inspect the "Solvent model" tab next to the output log.
3. Increase the input lowpass and estimate the scale again, and note if the solvent model estimation improves. 
4. Click the "Conf." tab of the viewer and inspect is OccuPy can adequately tell low-scale stuff from solvent. 

---

## 2. Open an existing solvent mask
OccuPy permits you to simply open an existing mask to use as the solvent definition, but it must be the same 
size as you input map. 

1. Click the "browse" button next to the "solvent def" drop-down menu below the viewer, and select the mask. 
2. Click the "Sol.def." tab in the viewer and inspect the map. 


---

## 3. Generate a solvent definition in the GUI
The scale is estimated independently form the solvent model, and can be thresholded or binarized to provide a 
solvent defintion. 

1. Make sure the appropriate input map is open and selected
2. Estimate the scale.
3. Click the "Sol.def." tab of the viewer and tick the checkbox "Binarize..."
4. Drag the slider to alter the binarization threshold. The aim is to segment solvent and non-solvent, but it does 
   not need to be very accurate. 
5. In the top menu, click "Run->Generate solvent definition from scale". This should create and save a solvent mask, 
   named by the threshold value. This file will also be loaded and selected in the "solvent def" dropdown.

---

## 4. Evaluate the solvent definition
To evaluate a solvent definition, we inspect the solvent model and resulting confidence. 

1. Make sure the appropriate input map is open and selected, then estimate the scale. 
2. Insepct the "Solvent model" tab next to the output log. The green parabola is fitted to the maked data histogram 
   in black, whereas the original data histogram is shown in grey. 
3. Click the "Conf." tab of the viewer and inspect is OccuPy can adequately tell low-scale stuff from solvent. 
   **Notice especially that the confidence might differ from the solvent definition, becasue OccuPy might estimate 
   components as significant even though you said they might be solvent.**

---

## 5. Use the solvent definition

1. Make sure the appropriate input map and solvent defintion are both selected.
2. Set the desired modification parameters.  
3. Click "Modify Map". 
4. Visualize the output by clicking "Launch ChimeraX"

---

## Final Notes
1. You can unselect a solvent definition by selecting the empty filed in the "solvent def" dropdown. A subsequent 
   run will not use any solvent definition.