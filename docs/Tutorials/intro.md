# An intro tutorial


This is a general tutorial to get acquainted with the GUI and workflow.

<div class="admonition hint">
<p class="admonition-title">There's something you should know</p>
<p>
It will be useful to read the GUI overview first, or refer to it through this tutorial.
</p>
</div>
<div class="admonition hint">
<p class="admonition-title">The devil is in the details</p>
<p>
There are more instructive tutorials for individual use cases, which also clarify limitations and effects of 
adjusting input parameters. It is recommended that you do this quick general tutorial first, then the specific 
ones.
</p>
</div>


---

## 1. Start OccuPy 
1. Open OccuPy by double-clicking the distributed binary or calling `occupy_gui` in a terminal. 

2. If you are unsure where the GUI will run and put output files, or want to change this, click "Session"->"Change 
location" in the top menu.

3. You will find three (3) large buttons above the ouput log, called "Estimate Scale", "Modify Map", and "Launch 
chimeraX". These should all be greyed out. Check that the far-right 
button to start ChimeraX does not indicate "(not found)". If ChimeraX was not found, you will not be able to invoke 
ChimeraX from the OccuPy GUI. Please see the section for 
<a href="../../Troubleshooting/chimX_trbl/">troubleshooting chimeraX</a> to remedy this, or use the workaround below. 
<div class="admonition hint">
<p class="admonition-title">Workaround</p>
<p>
OccuPy writes a chimeraX command script (.cxc) every time you estimate the scale or modify a map. You can open 
this through chimeraX instead of using OccuPy to launch chimeraX. <strong> Just make sure to use "File"->"close 
session" in chimeraX before you open the .cxc-file written by OccuPy. </strong>
</p>
</div>

---

## 2. Open a map 
1. To open an input file we would normally click "browse" in the top-right corner of the OccuPy window. For this 
   tutorial we will use a map from the emdb instead. Click the "emdb" button in the top-right corner of the OccuPy 
   window. A small dialog should open asking to specify the unique ID of the map in the electron microscopy database. 
2. Enter the number 3061 and click "Fetch". This will download, unzip and open a relatively small map of the 
   transmembrane protein gamma-secretase in the current working directory.
3. In the "Input" tab of the viewer, the input map can be inspected. Just below the viewer, select the z-dimension and 
   change the slice number to 96 to see the transmembrane helices across the light-grey detergent micelle, as well 
   as the extracellular domain. 

---

## 3. Notice the kernel settings 
Based on the input, reasonable kernel settings were derived automatically. In this case, 

- a low-pass of 8Å will be applied to make solvent estimation easier.
- a sphere with radius 2.86Å will be used to estimate the local scale. 
- a cube of 5 pixels (voxels) in each dimension will hold a binary mask with the above radial cutoff. 
- of all the pixels selected by the binary mask, the scale will be proportional to the bottom 96.47% percentile, or 
  the top 3.53% percentile
- the above parameters results in 93 pixels (voxels) being sampled around each map pixel (voxel).
- a region of 12 pixels (voxels) in each dimension will be used to determine the scale-normalizing value. This value 
  is always 12 by default, and not estimated. 

**Do not change these settings for this tutorial.**

---

## 4. Estimate resolution-mode local scale 
1. Make sure "resolution" is checked under the "Modification options". 

2. Run OccuPy by clicking the Big button labeled "Estimate scale" just above the output log. 

3. This should finish in a few seconds. Notice that the run is individually numbered as "1-1" in the output log. 

<div class="admonition attention">
<p class="admonition-title">There's more to this</p>
<p>
To learn how parameter adjustment can help you get a better estimate, consult the 
<a href="../case/est_res">tutorial on relative resolution estimation</a> later.
</p>
</div>

---

## 5. Assess the scale 
1. You will find that the estimated scale has been added to the "scale map" drop-down and is thus also rendered in the 
viewer tab "Scale". Click this viewer tab and drag the slider to check the estimated scale. 

2. To further inspect the local scale, click the big button labeled "Launch ChimeraX" to the far right above the output 
log. This will launch chimeraX and run a command script written by OccuPy the last time you ran anything 
through the GUI. In this case you should see the input map colored by the estimated scale, along with a color key.

3. Change the color of map #1 to grey. Next, in the chimeraX command-line tool, run the command 
`scale_color #1 #2`. This will re-color map #1 by the estimated scale (map #2), according to the color key. 

4. Close chimeraX.

---

## 6. Assess the solvent model
1. The solvent model is ony used for modification, but it is nonetheless a good idea to check it. Click the tab 
   "Solvent model" next to the "output log" tab at the bottom of the OccuPy GUI. The green line is the solvent model
   fit as a gaussian to the map histogram. It appears parabolic since this is a log-plot. The red line is the 
   confidence of voxel values above solvent. 

2. Because we have a solvent model, we also have a confidence map. This has been opened in the viewer tab "Conf.". 
   Click  this tab and inspect what occupy thinks is solvent. You should find that the detergent is also identified 
   as "stuff" (being white), as opposed to solvent (black). 

---

## 7. Estimate occupancy-mode local scale 
1. Click on the "amplify" tab of modification options on the left. Enable it and drag the slider. The "plot" tab in the 
viewer should update interactively, showing you how scale will be modified in the output compared to the input. 

2. Click on the "Preview" tab of the viewer. There should be a notice to the effect that this is a bad idea. This is 
   because the scale we have estimated includes contrast degradation due to poor resolution and flexibility. OccuPy 
   does not allow you to use this for modifying maps, because it can't "compensate" for flexibility.  The big button 
   "modify map" should also be inactivated. 

3. When you enabled any modification, the scale-mode just below the modification options was changed to "occupancy" and 
   can't be changed as long as you want to modify. This is again because OccuPy can't modify poor resolution, so 
   it forces occupancy-mode. Click "Estimate scale" again to estimate the occupancy-mode local scale. This should 
   take a few seconds and then the new scale should be selected in the "scale map" drop-down menu, now containing 
   "occ" in its name. 
<div class="admonition attention">
<p class="admonition-title">There's more to this</p>
<p>
To learn how parameter adjustment can help you get a better estimate, consult the 
<a href="../case/est_occ">tutorial on occupancy estimation</a> later.
</p>
</div>
---

## 8. Modify by local scale

1. Click the "Preview" tab of the viewer. Note that this preview is rough. 

2. Try to remove the membrane by enabling attenuation and inspecting the preview as you alter the attenuation 
   power by dragging the slider.
3. Try the same by sigmoid modification. Note that sigmoid has two parameters. 
4. Select the "plot" tab of the viewer to see how these modifications would alter the scale of the output compared to 
   input. Where the colored line is below the dashed line, scale will be attenuated. Converesely, where the line is 
   above the dashed line, scale will be amplified. 
5. Click the button "modify Map" to generate all desired modifications. 
6. When completed, **the preview is still just a preview**. To see the output, please click "Launch ChimeraX". This 
   will open the original map and all modifications, but **only the original is visible by default**. Read on.
<div class="admonition attention">
<p class="admonition-title">There's more to this</p>
<p>
To understand map modification, consult the 
<a href="../case/modification">tutorial on map modification</a> later.
</p>
</div>
---

## 9. Inspect modification in ChimeraX
1. Change the level (threshold) of the input and all modified maps to 0.06 by using the chimeraX command-line tool to 
   run 
   `occupy_level 0.06` .
2. Check the difference between the modifications, comparing to the "plot" tab in the OccuPy GUI. 
3. Close ChimeraX 

## 10. Final notes 
1. Click "Session->View full log" in the menu field. Note that all run setting have been saved according to the same 
   unique run-ID that you saw in the output log. This log is persistent. If you close OccuPy and start it again, the 
   numbers will be incremented, and everything you did before and do now will be in the full log. 
2. Maps are over-written by default. If you alter the input lowpass to 10Å and re-estimate local scale, the 
   previously estimated scale is gone. But the parameters to re-generate it is in the full log, provided that you 
   know the run ID. 
3. You might want to play with a few more instructive maps. Here are a few entries that might be interesting to test 
   OccuPy. Remember to use the emdb-fetch button in the GUI, or the `--emdb <ID>` flag on the command-line.

   | Entry                                         | Sample                         | Box-size |
---|-----------------------------------------------|--------------------------------|----------|
   | [27842](https://www.ebi.ac.uk/emdb/EMD-27842) | Twinkle helicase               | 320      |
   | [30185](https://www.ebi.ac.uk/emdb/EMD-30185) | F-actin                        | 320      |
   | [33437](https://www.ebi.ac.uk/emdb/EMD-33437) | RNA polymerase II + nucleosome | 240      |
   
