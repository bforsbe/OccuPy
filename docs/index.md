# Overview
<div class="c-compare" style="--value:20%; --h:4.6; --w:16;">
  <img class="c-compare__left" src="https://drive.google.com/uc?export=view&id=1ztTefAhILu648oBNr9bFB1sZD31tNH3a" 
alt="Synthetic occupancy model" />
  <img class="c-compare__right" src="https://drive.google.com/uc?export=view&id=19U1PaDpn6e4dVtVMC91QXVy3JUtrPfOW" 
alt="Synthetic map estimate" />
  <input type="range" class="c-rng c-compare__range" min="0" max="100" value="20" oninput="this.parentNode.style.
setProperty('--value', `${this.value}%`)" />
</div>

## What is OccuPy

The primary purpose of OccuPy is to estimate the local scale of cryo-EM maps. 
<br><br>
What does the 'local scale' 
mean? In simple terms, think of it as the range of pixels values. In well-resolved regions, contrast is high, and we 
expect very bright and very dark pixels. If that region has decreased resolution or occupancy, we expect decreased 
contrast and a narrower range of pixel values. The limit is solvent, which has Gaussian distribution. OccuPy was built to estimate this 'scale', to quantify relative contrast degradation. This means that it can 
estimate the relative resolution, or occupancy. OccuPy also uses this scale as a tool for map modification. 

<p>
 <em>
  <br>
In essence, OccuPy locates the region that exhibits the highest range of pixel values, and utilizes this to place 
all other regions on a nominal scale between 0 and 1.
  <br>
 </em>
</p>



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

## The gist 
OccuPy is currently implemented as a GUI and command-line tool using open-source python libraries, to facilitate 
visualization of partial occupancy and the relative resolution of cryo-EM reconstructions by e.g  implementing map 
modification as spatial filtering based on the estimated partial occupancy of local map components. 
This is intended to create maps that emulate reconstruction expected if the input (image) data was more 
homogenous at lower or higher occupancy.

