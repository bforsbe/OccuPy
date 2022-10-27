# Estimate relative resolution


<div class="admonition hint">
<p class="admonition-title">Recommendation</p>
<p>
Please read the GUI overview and conduct the intro tutorial first.
</p>
</div>

OccuPy was not designed to accurately quantify local resolution, but rather to try to disregard contrast attenuation 
due to solely to variations in e.g. flexibility. It will however accurately estimate **relative** local resolution, 
which might inform you on what parts are consistent and favoured for alignment. This includes **all** effects, so 
think of it as a quality estimate of the map, rather than resolution. 

Other tools are available to estimate resolution on an absolute scale, which might be more suitable to use. The 
benefit of OccuPy is that it is fast and easy to use and adjust, so that it's easier to use for qualitative map 
analysis. 

<div class="admonition attention">
<p class="admonition-title">This is not absolute resolution</p>
<p>
You will not get a number that corresponds to the resolution at each point in the map. You will get a "quality" 
score that tells you how well resolved each region is, compared to the best resolved region.
</p>
</div>

---

## 1. First pass estimate
1. Open the input map. 
2. Set the scale mode to "resolution" and estimate the scale. 
3. Click the button "Launch ChimeraX" to view the output. 

---

## 2. Sanity check
1. Check that the output log does not show any warnings (or errors).

---

## 3. Evaluate Kernel settings
Strong scatterers, variations in resolution, or any of a number of other factors may cause strong contrast. This 
means that the signal-to-noise ratio (SNR) is higher, which according to typical cryo-EM estimates more confidence in 
the estimated resolution, but not necessarily higher resolution. OccuPy evaluates contrast, which will be in 
proportion to SNR, which is thus not ideal for estimating resolution. It is thus prudent to be cautious, but OccuPy was 
built to be robust to outliers so with caution everything should be fine. Some settings may need be adjusted, nearly 
identically to that described in the tuorial to estimate occupancy. When you explore settings to increase the 
utility (and possibly also the fidelity) of the resolution estimate, note that this creates confirmation bias in 
the results based on your expectations. **Always report the kernel settings** used, which are documented in the full 
GUI log, or through command line by using `--verbose`. 

To evaluate a new kernel setting, re-estimate the scale and inspect the "Scale" tab of the viewer. You can also 
re-name the file "scale_res_<input_file_name\>.mrc" and open it manually in a ChimeraX-session opened through the GUI.
Remember to use the chimeraX command-line tool to run "scale_color #1 #<new scale map>" to color the input map by 
the new scale.

---

### 3.1 Input lowpass 
The input lowpass is inconsequential for the resolution estimation. 

---

### 3.2 The Kernel radius and size
These define the region around each pixel where OccuPy determines the local scale. That is, the define what "local" 
means. The kernel size is the maximum box dimension, and the radius is that of a spherical mask placed at the center 
of that box. The kernel is determined as the intersection of these. the number of voxels in this intersection is 
shown as the number of samples. 

<div class="admonition tip">
<p class="admonition-title">Gist</p>
<p>
The larger the kernel, the more samples and statistical certainty. <br>
The larger the kernel, the more you average the estimate. <br>
The kernel can typically be very small without problem.
</p>
</div>

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

<div class="admonition tip">
<p class="admonition-title">Gist</p>
<p>
Reducing the tau percentile will increase the resolution estimate (as in the estimate will indicate better 
resolution) of all regions, and vice versa. <br>
Tau is automatically calculated to minimize both over- and under-estimation. 
</p>
</div>
Look at the "Scale" tab of the viewer. In your scale estimate...

1. is homogeneous and nearly all white, then you might have a very homogeneous resolution. If you want to push the 
   relative resolution into a range where you might tell components apart, try increasing the tau percentile an 
   re-estimate the scale.
2. is only white for a very small region that does not correspond to what you would expect to be at "best resolution", 
   try reducing the tau percentile. It might also be better to adjust the tile-size as we will soon discuss, and use 
   the theoretically derived value for tau.

### 3.4 Tile size
OccuPy normalizes the estimated scale against a region of the map where it in some sense finds maximal contrast. The 
size of this region defines the size of the "best resolution" region. This region can be chosen smaller than you 
"best-resolution component", but if you make it too small then variations in atomic mass might start to affect the 
estimate. 

<div class="admonition tip">
<p class="admonition-title">Gist</p>
<p>
Increasing the tile size will reduce the influence of high local mass, and vice versa. <br>
Setting the tile-size too large will cause systematic over-estimation of local scale. 
</p>
</div>

Look at the "Scale" tab of the viewer. In your scale estimate...

1. is only white for a very small region that does not correspond to what you would expect to be at the best 
   resolution, try increasing the tile-size. 

---

### Final notes
1. Because a reduced tile-size emphasizes variations in mass even when resolution is the same, a much reduced tile 
   size is potentially useful to estimate relative mass or occupancy when the relative mass is known, but for 
   resolution estimation it does not make much sense to reduce it too far.
