# Modify a map 

<div class="admonition attention">
<p class="admonition-title">You need an occupancy estimate</p>
<p>
Please conduct the tutorial to estimate occupancy before this toturial.
You will use the same parameters to modify as accurately as possible
</p>
</div>

Map modification in OccuPy aims to alter the occupancy of map components. The output aims to emulate the 
reconstruction that is expected if the input data had been more homogeneous, at either lower or higher occupancy.  

---

## 1. Optimize parameters

For fidelity of the modified map (as representing something genuinely possible given the data that was used to make 
the input map) the occupancy should be as accurate as possible. The tutorial on occupancy esstimation guides you to 
do so. In some cases you may just want to achieve a given effect. It's up to you. But determine the scale kernel 
settings you want, and enter them in the GUI, starting from the top down to avoid re-estimation of values you've 
entered. 

---

## 2. Validate the solvent model
<div class="admonition danger">
<p class="admonition-title">No joke</p>
<p>
This is neccessary. Do not skip it. You are not saving time by doing so.
</p>
</div>
To reduce amplification of noise, OccuPy does not permit modification where the confidence over solvent is low. The 
confidence depends on the solvent model, which fits a Gaussian to the solvent peak of the map histogram. 

1. Check the solvent model tab next to the output log. You want to see that the green parabola coincides well with 
   the solvent peak around ~0, and that it drops significantly faster than the voxel intensity distribution in black.
   If not, you may need to low-pass the input to a higher value as in step 2 of this tutorial, or use a solvent 
   definition as per this other tutorial. 
2. Click the confidence tab of the viewer labeled "Conf.", and inspect it. Toggle between this tab and the input to 
   evaluate how well the confidence was estimated.

If the solvent model look bad and/or the confidence map does not cover the regions of the map that you are 
interested in modifying, you will need to alter settings and/or input to achieve a more permissive confidence map. 
There are two principal strategies: 

1. Create a solvent definition. There is a separate tutorial for this. 
2. Alter the input lowpass setting. If you have just optimized your scale-kernel settings, this might be annoying.

---

## 3. Estimate occupancy
Make sure occupancy-mode is selected just below the modification tabs, and click "Estimate scale". This will 
re-estimate and set the occupancy-mode estimate as active.

---

## 4. Optimize modification
Consider which modification to use. More than one type can be generated at the same time to generate multiple output 
maps. The effect of multiple modification types are not additive, i.e. they are not compounded or combined.

=== "Amplify"

    Amplification will effectively make low-occupancy components higher. The output map scale will be mapped by a 
    an inverse power-scaling, which the user specifies. A power of 1 thus means that the output scale is the same as 
    the input, which would leave the output map identical to the input. Higher values signify stronger amplification, 
    and values in the range 2-5 are typically useful. Higher values approach equalization, which emulates full 
    occupancy at all non-solvent points.
   
    <div class="admonition note">
    <p class="admonition-title">Amplification</p>
    <p>
    Amplification is useful to visualize a map with weak components at a single threshold. 
    </p>
    </div>

=== "Attenuate"

    As amplification, but with a (non-inverse) power scaling. Again, a power of 1 means that the output scale is the 
    same as the input, which would leave the output map identical to the input. Higher values signify stronger 
    attenuation, and values in the range 2-5 tend to be useful. Higher values leave only full occupancy regions, 
    effectively removing any other regions.
   
    <div class="admonition note">
    <p class="admonition-title">Attenuation</p>
    <p>
    Attenuation is useful to visualize a map with uninteresting weaker components, by removing them. Detergent belts is 
    a good example.
    </p>
    </div>

=== "Sigmoid"

    The sigmoid modification combines attenuation of lower-scale components with amplification of higher scale 
    components. Again, a power of 1 means that the output scale is identical to the input, and no modification will 
    occur. The sigmoid modification takes a second parameter, which we call pivot. The pivot value is the threshold 
    scale value that will remain unchanged. Regions where the scale was estimated above the pivot will be amplified, 
    and conversely regions with scale lower than the pivot will be attenuated. 
   
    <div class="admonition note">
    <p class="admonition-title">Sigmoid</p>
    <p>
    Sigmoid modification is useful to visualize a map with flexible components, by removing them while still amplifying 
    relevant structured components. 
    </p>
    </div>

1. Click the selected modification type tab under "Modification options", and enable it. 
2. Increase the power of the modification to a value above 1. This will alter 
    - the "plot" tab of the viewer. This shows how the output map scale will depend on the estimated (input) scale. 
      It is useful to look at this tab while changing the parameters to get a sense of sensitive the modification is 
      to changing the modification settings.  
    - the "preview" tab of the viewer. This will show a rough preview of what the output will be. It is not as 
     accurate, and does not consider the confidence map. It will therefore look fairly noisy. It is very useful to 
      look at this tab when changing the modification settings. 
    <div class="admonition attention">
    <p class="admonition-title">Dont't trust the preview </p>
    <p>
    Don't optmize the modification based <strong>only</strong> on the preview. Get it roughly right, and continue the 
    tutorial.  
    </p>
3. If using sigmoid modification, the pivot should also be tuned. This is arguably the most important setting for 
   sigmoid modification, as it determines a threshold scale value that is not modified. Values below are attenuated, 
   and values above are amplified. 
4. Once modification has been determined roughly, click "Modify Map".
5. Once OccuPy returns, click "Launch chimeraX", or open chimeraX and open the most recent .cxc-file written in the  
   directory where occupy is running. 
6. In chimeraX, only the input map is visualized by default, and is colored by the estimated scale. Show the 
   modified map and compare to the input map. You can alter the threshold value of the input map and any modified 
   map at the same time by using the command ```occupy_level <value>```. Compare the maps and evaluate if 
   modification should be altered. 
7. Close chimeraX, alter modification parameters, and click "Modify Map" again, followed by "Launch chimeraX". 
8. Repeat step 7 until satisfied. 

## 5. Finalize 
There are two optional/extra settings worth considering when generating the final output 
### 5.1 Suppress solvent? 
The solvent noise of the input map is included in the modified output by default, because OccuPy aims to emulate 
realistic reconstructions given homogeneous input data. However, if modification is used for visualization and the 
solvent model is accurate, solvent noise might only be a nuisance. 
### 5.1 Lowpass output? 
Modification does alter map constituents and may increase noise. Low-pass filtration of the output might be a good 
idea. It can also be used to verify the estimated occupancy, as detailed in the tutorail on occupancy estimation.  
    
