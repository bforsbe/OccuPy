# Estimate occupancy 

<style>
p.comment {
background-color: #c3c8e8;
color: #4051b5;
padding: 10px;
margin-left: 0px;
border-radius: 5px;
}

</style>

<p class="comment">
Please read the GUI overview and conduct the simple tutorial first.
</p>

To estimate occupancy we must try to remove contrast degradation due to e.g. flexibility. Even this is possible to 
achieve perfectly, you should think of the estimate as relative, in the sense that lower occupancy regions is 
confidently lower than those estimated higher, but that there is an unquantified uncertainty to the estimated 
occupancy as an absolute number. 

The following steps highlight factors influencing this, and how to make the necessary adjustments to fit your purpose. 

---

## 1 First pass estimate
1. Open the input map. 
2. Set the scale mode to "occupancy" and estimate the scale. 
3. Click the button "Launch ChimeraX" to view the output. 

---

## 2 Sanity check
1. Check that the output log does not show any warnings (or errors).
2. Check the "Conf." tab in the viewer. It should be white where there is "stuff", and black where there is solvent. 
   If this si not the case, your solvent model might be bad. This is not an issue for occupancy estimation, but it 
   will be if you want to modify later. If ypu just want to estimate occupancy, go to step 3. Otherwise, check the 
   solvent model on the tab next to the output log. The green parabola should fit the histogram solvent peak near 0 
   quite well and drop faster than the histogram. If not, you may need to increase the input lowpass cutoff in the 
   kernel settings, or even use a solvent definition. There  is a dedicated tutorial for this, that you should do 
   first if you think this might be necessary. 

---

## 3 Evaluate Kernel settings
Strong scatterers, variations in resolution, or any of a number of other factors may cause an unreasonable occupancy 
estimate based on your expectation and the assumptions OccuPy is built on. You can explore settings to increase the 
utility (and possibly also the fidelity) of the occupancy estimate, but note that this creates confirmation bias in 
the results based on your expectations. **Always report the kernel settings** used, which are documented in the full 
GUI log, or through command line by using `--verbose`. 

To evaluate a new kernel setting, re-estimate the scale and inspect the "Scale" tab of the viewer. You can also 
re-name the file "scale_occ_<input_file_name\>.mrc" and open it manually in a ChimeraX-session opened through the GUI.
Remember to use the chimeraX command-line tool to run "scale_color #1 #<new scale map>" to color the input map by 
the new scale.

### 3.1 Input lowpass 
The input lowpass cutoff is used to neutralize resolution-dependent effects, but does introduce some spatial 
correlation, so that the local occupancy is averaged. If your **input map**...

1. **is higher resolution than the cutoff**:  Try reducing this number, which will give you better resolution in the 
    scale estimate. See also point 2.
2. **has components resolved worse than the cutoff**: Increase the lowpass frequency to make sure all the occupancy 
   is estimated at the same resolution in all parts of the map.

---

### 3.2 The Kernel radius and size
These define the region around each pixel where OccuPy determines the local scale. That is, the define what "local" 
means. The kernel size is the maximum box dimension, and the radius is that of a spherical mask placed at the center 
of that box. The kernel is determined as the intersection of these. the number of voxels in this intersection is 
shown as the number of samples. 

<p class="comment">
The larger the kernel, the more samples and statistical certainty. <br>
The larger the kernel, the more you average the estimate. <br>
The kernel can typically be very small without problem.
</p>

Look at the "Scale" tab of the Occupy viewer. If your scale estimate...

1. Looks like "blocks", then the kernel size is much smaller than the radius. This is not a problem, but you could 
   reduce the radius to define a more spherical region around each map location. 
2. Looks much lower resolution that the input map, then you might do well to reduce the kernel size and radius. 

---

### 3.3 Tau percentile
To reduce the influence of voxel-value outliers in the scale estimate, some voxel values are always "rejected". The tau 
percentile defines how many sample values should be rejected. The value of tau is optimally calculated based on your 
kernel settings (to reduce the probability of over- and under-estimating the scale), so you should not change it 
unless you have good reason to do so. **Always report the kernel settings**

<p class="comment">
Reducing the tau percentile will increase the occupancy estimate of all regions, and vice versa. <br>
Tau is automatically calculated to minimize both over- and under-estimation. 
</p>
Look at the "Scale" tab of the viewer. In your scale estimate...

1. is homogeneous and nearly all white, then you might have a very homogeneous occupancy. If you want to push the 
   relative occupancy into a range where you might tell components apart, try increasing the tau percentile an 
   re-estimate the scale. **This is no longer a good approximation of absolute occupancy**
2. is only white for a very small region that does not correspond to what you would expect to be at full occupancy, 
   try reducing the tau percentile. It might also be better to adjust the tile-size as we will soon discuss, and use 
   the theoretically derived value for tau.

---

### 3.4 Tile size
OccuPy normalizes the estimated scale against a region of the map where it in some sense finds maximal contrast. The 
size of this region defines the size of the "full occupancy" region. This region can be chosen smaller than you 
full-occupancy component, but if you make it too small then variations in atomic mass might start to affect the 
estimate. 

<p class="comment">
Increasing the tile size will reduce the influence of high local mass, and vice versa. <br>
Setting the tile-size too large will cause systematic over-estimation of local scale. 
</p>
Look at the "Scale" tab of the viewer. In your scale estimate...

1. is only white for a very small region that does not correspond to what you would expect to be at full occupancy, 
   try increasing the tile-size. 

---

### Final notes
1. Because a reduced tile-size emphasizes variations in mass even when occupancy is the same, a much reduced tile 
   size is potentially useful to estimate relative mass or occupancy when the relative mass is known. There are 
   however better methods available for this purpose, which we recommend for accurate estimation. OccuPy simply 
   exposes these methods where they might be relevant for fast and highly resolved estimation in the absence of 
   ground-truth mass. 

