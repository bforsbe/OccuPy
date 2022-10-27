# Supress solvent

<div class="admonition hint">
<p class="admonition-title">Recommendation</p>
<p>
Please read the GUI overview and conduct the intro tutorial first.
</p>
</div>


To accurately suppress solvent you primarily have to make sure that the solvent model and confidence is accurate. 
The following steps highlight factors influencing this, and how to make the necessary adjustments. 

---

## 1. Set up the run
1. Open the input map. 
2. Set the desired scale mode and estimate the scale. We don't need the scale at this point, but estimating it will 
   also generate the solvent model and confidence. 
3. Check the solvent model tab next to the output log. You want to see that the green parabola coincides well with 
   the solvent peak around ~0, and that it drops significantly faster than the voxel intensity distribution in black.
   If not, you may need to low-pass the input to a higher value as in step 2 of this tutorial, or use a solvent 
   definition as per this other tutorial. 
4. Click the confidence tab of the viewer labeled "Conf.", and inspect it. Toggle between this tab and the input to 
   evaluate how well the confidence was estimated.  

---

## 2. Try different low-pass settings.
The input low-pass setting at the top of the kernel settings is applied before solvent model fit, because it reduces 
the variance of the solvent noise more than anything else. By increasing it, the solvent peak tends to become more 
prominent.

1. Increase the kernel setting "Input lowpass" by a few Å. 
2. Estimate the scale again.
3. Evaluate the confidence and solvent model again, and adjust input lowpass as appropriate. When you are happy, 
   proceed to step 3.

---

## 3. Generate output
1. Tick the check-box in the "Optional/extra" section on the bottom left. 
2. To suppress solvent on the input map without any other modifications, click "Estimate Scale".
3. To suppress solvent of any modified map, click "Modify Map" to perform both operations. 
4. Visualize the output by clicking "Launch ChimeraX"

---

## Final notes 

1. The confidence map is written as an auxiliary file. You Can open it manually in the chimeraX-session to have a loof 
at it if you want. You can modify and use it as a mask for other purposes as well. But beware that it will be 
over-written the next time you estimate the scale or modify any map, unless you change its name. 
2. There is no way to 
provide OccuPy with a confidence, it will estimate this internally each time.
