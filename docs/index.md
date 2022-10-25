# Overview

---

## What is OccuPy

The primary purpose of OccuPy is to estimate the local map scale of cryo-EM maps. 

What does the 'local scale' 
mean? In simple terms, think of it as the range of pixels values. In well-resolved regions, contrast is high, and we 
expect very bright and very dark pixels. If that region has decreased resolution or occupancy, we expect decreased 
contrast and a narrower range of pixel values. The limit is solvent, which has Gaussian distribution. OccuPy was built to estimate this 'scale', to quantify relative contrast degradation. This means that it can 
estimate the relative resolution, or occupancy.

**In essence, OccuPy locates the region that exhibits the highest range of pixel values, and utilizes this to place 
all other regions on a nominal scale between 0 and 1.**

OccuPy also uses this scale as a tool for map modification. 

### Disclaimer


<div class="admonition warning">
<p class="admonition-title">SPA or STA, but no single tomo</p>
<p>
OccuPy is only applicable to reconstructions produced by ensemble averaging, like SPA and STA. 
<br>
That is, it is incompatible with analysis of a single tomogram.
</p>
</div>

<div class="admonition warning">
<p class="admonition-title">This is not postprocessing</p>
<p>
OccuPy  does not sharpen maps. It tries not to.
</p>
</div>

<div class="admonition warning">
<p class="admonition-title">No number for your abstract</p>
<p>
OccuPy will not provide an absolute local resolution in Å, only a relative local resolution. 
</p>
</div>

---

## Why estimate local scale?
The local scale contains information about both resolution and occupancy. With this in mind, OccuPy is designed to 
estimate the local scale

- extremely fast
- without half-sets
- without GPUs
- without masks

The reason for this is that it is intended to be compatible with the expectation maximization (fast) maximum likelihood 
classifiers (no half-sets) based on prior alignments (no GPUs), and be compatible with unbiased discovery of 
macromolecular heterogeneity and/or components (no masks). In this context, it will provide ways to weight data 
and/or provide a displacement vector to emphasize macromolecular resolution and/or occupancy during gradient 
descent. Basically, it needs to be fast enough to run repeatedly without delaying processing, and simple enough to 
use that it needs no input other than a cryo-EM map. 

It is here implemented as a command-line tool using open-source python libraries, to facilitate visualization of 
partial occupancy and the relative resolution of cryo-EM reconstructions.

---

## Modification of partial occupancies
OccuPy implements map modification as spatial filtering based on the estimated partial occupancy of local map 
components. This is intended to create maps that emulate reconstruction expected if the input (image) data was more 
homogenous at lower or higher occupancy. There are three modes. 

### Mode 1  - Amplification
Amplification will effectively make low-occupancy components higher. The output map scale will be mapped by a 
an inverse power-scaling, which the user specifies. A power of 1 thus means that the output scale is the same as the 
input, which would leave the output map identical to the input. Higher values signify stronger amplification, and 
values in the range 2-5 are typically useful. Higher values approach equalization, which emulates full occupancy at all 
non-solvent points.

<div class="admonition note">
<p class="admonition-title">Amplification</p>
<p>
Amplification is useful to visualize a map with weak components at a single threshold. 
</p>
</div>

### Mode 2 - Attenuation
As amplification, but with a (non-inverse) power scaling. Again, a power of 1 means that the output scale is the 
same as the input, which would leave the output map identical to the input. Higher values signify stronger attenuation, 
and values in the range 2-5 tend to be useful. Higher values leave only full occupancy regions, effectively removing 
any other regions.

<div class="admonition note">
<p class="admonition-title">Attenuation</p>
<p>
Attenuation is useful to visualize a map with uninteresting weaker components, by removing them. Detergent belts is 
a good example.
</p>
</div>

### Mode 3 - Sigmoid 
The sigmoid modification combines attenuation of lower-scale components with amplification of higher scale 
components. Again, a power of 1 means that the output scale is identical to the input, and no modification will 
occur. The sigmoid modification takes a second parameter, which we call pivot. The pivot value is the threshold 
scale value that will remain unchanged. Regions where the scale was estimated above the pivot will be amplified, and 
conversely regions with scale lower than the pivot will be attenuated. 

<div class="admonition note">
<p class="admonition-title">Sigmoid</p>
<p>
Sigmoid modification is useful to visualize a map with flexible components, by removing them while still amplifying 
relevant structured components. 
</p>
</div>