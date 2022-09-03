# OccuPy
A fast and simple python module and program to estimate local scaling of cryo-EM maps, to approximate 
occupancy, and optionally also equalise the map according to occupancy while suppressing solvent amplification.

![image](https://drive.google.com/uc?export=view&id=14jbTq32VDkzoF0O59Bzb7cXf4cjlBFrx)

## Estimation of local scale/occupancy 
The primary purpose of **OccuPy** is to estimate the local map scale of cryo-EM maps. What does the 'local scale' 
mean? In simple terms, think of it as the range of pixels values. In well-resolved regions, contrast is high, and we 
expect very bright and very dark pixels. If that region has decreased resolution or occupancy, we expect decreased 
contrast and a narrower range of pixel values. The limit is solvent, which has Gaussian distribution. **OccuPy** was 
built to estimate this 'scale' under the assumption that structural variability (flexibility) is negligible (in which 
case it is a good approximation for occupancy), and to modify the estimated scale while not modifying solvent noise. 
In essence, **OccuPy** locates the region that exhibits the highest range of pixel values, and utilizes this to place 
all other regions on a nominal scale between 0 and 1. 

### Disclaimer
**OccuPy** does not sharpen maps. It tries not to.

**OccuPy** does not estimate the local resolution, but might correlate with it.

## Why estimate local scale?
**OccuPy** is designed to work
- extremely fast
- without half-sets
- without GPUs
- without masks

The reason for this is that it is intended to be compatible with the expectation maximization (fast) maximum likelihood 
classifiers (no half-sets) based on prior alignments (no GPUs), and be compatible with unbiased discovery of 
macromolecular heterogeneity and/or components (no masks).
In this context, it will provide a displacement vector to emphasize macromolecular occupancy during gradient descent.
Basically, it needs to be fast enough to run repeatedly with delaying processing, and simple enough to use that it 
needs no input other than a cryo-EM map. 

It is here implemented as a command-line tool using open-source python libraries, to facilitate visualization of 
partial scale of cryo-EM reconstructions.

## Modification of partial occupancies 
**OccuPy** can also amplify confidently estimated partial occupancy (local scale) in the input map by adding the 
`--amplify` or `--attenuate` option. To modify, one must also specify `--gamma`, which in simple terms is the power 
of the modification, analogous to a traditional gamma correction factor. `--gamma 1` means to do nothing, and higher 
values signify stronger modification. Values higher than about 50 are largely pointless, as values in the range 2-5 
are typically useful. A *very* high (limiting) limiting value of `--gamma 50` (or more) leads to 
- **amplification**: full occupancy at all non-solvent points.
- **attenuation**:   no occupancy at all non-solvent points where estimated scale was less than 100%.

NOTE: Values lower than 1 are not permitted, as it simply inverts the relationship between amplification and 
attenuation. 

## Solvent suppression 
Map scale amplification by inverse filtering would result in an extremely noisy output if solvent was permitted to 
be amplified. To mitigate this, **OccuPy** estimates a solvent model which limits the amplification of regions where 
the map scale is estimated as near-solvent. One can aid this estimation by providing a mask that covers non-solvent, 
permitting **OccuPy** to better identify solvent. This need not be precise or accurate, and **OccuPy** will amplify map 
scale outside this region if it is confident about the scale in such a region . This is thus *not* a solvent mask in 
the traditional sense, but rather a solvent definition. Additionally, the estimation of the solvent model does NOT 
affect the estimated map scaling in any way, only the optional amplification.

The suppression of solvent is not contingent on amplification - one can choose to supress solvent regions or not, 
irrespective of amplification. This acts as automatic solvent masking, to the extent that  **OccuPy** can reliably 
detect it.

## Expected input 
**OccuPy** expects an input map that has not been solvent-flattened (there should be some solvent somewhere in the map, 
where more is better). **OccuPy** may also work poorly where the map has been post-processed or altered by 
machine-learning, sharpening, or manual alterations. It has been designed to work in a classification setting, and as such does *not* 
require half-maps, a resolution estimate, or solvent mask. It will likely benefit if you are able to supply these 
things, but does not need it. 

## Installation
`OccuPy` can be installed from the [Python Package Index](https://pypi.org/) (PyPI)

```shell
pip install occupy
```
But one may also pip install from the cloned repo

```shell
$ git clone https://github.com/bforsbe/OccuPy.git
$ cd occupy 
$ pip install -e . 
```

## Usage

`OccuPy` is a command-line tool 

```shell
$ OccuPy --version
OccuPy: 0.1.4
```

but the tools and functions are available from within a python environment as well

```shell
In[1]: import occupy

In[2]: occupy.occupancy.estimate_confidence?                                                                                            
Signature:
occupy.occupancy.estimate_confidence(
    data,
    solvent_paramters,
    hedge_confidence=None,
    n_lev=1000,
)
Docstring:
Estimate the confidence of each voxel, given the data and the solvent model

The estimate is based on the relative probability of each voxel value pertaining to non-solvent or solvenr model

:param data:                input array
:param solvent_paramters:   solvent model parameters, gaussian (scale, mean, var)
:param hedge_confidence:    take the estimated confidence to this power to hedge
:param n_lev:               how many levels to use for the histogram
:return:
File:      ~/Documents/Occ/occupy/occupy/occupancy.py
Type:      function

In[3]:

```

## Examples of use
### Estimating and modifying local map scale 

In its basic form, **OccuPy** simply estimates the map scale, writes it out along with a chimeraX-command script to 
visualise the results easily

```shell
$ OccuPy -i map.mrc 
$ ls  
map.mrc    scale_map.mrc    chimX_map.cxc
```

To modify all confident partial scale regions (local partial occupancy), use `--amplify` and/or  `--attenuate` 
along with `--gamma` as described above. Because the input is modified and not just estimated, there is now additional 
output map(s). 
```shell
$ OccuPy -i map.mrc  --amplify --gamma 4 
$ ls  
map.mrc    scale_map.mrc    ampl_4.0_map.mrc    chimX_map.cxc
```

To supress (flatten) solvent content use `--exclude-solvent`
```shell
$ OccuPy -i map.mrc --exclude-solvent 
$ ls  
map.mrc    scale_map.mrc    solExcl_map.mrc    chimX_map.cxc
```
These can also be combined, of course
```shell
$ OccuPy -i map.mrc --exclude-solvent --attenuate --amplify --gamma 4
$ ls  
map.mrc    scale_map.mrc    ampl_4.0_solExcl_map.mrc   attn_4.0_solExcl_map.mrc    chimX_map.cxc
```
## Visualising the local scale
The easiest method of visualizing the estimated local scale is to use the chimeraX command script output by `OccuPy`. 
This will 
1. Color the input (and any output) map by the estimated scale
2. Provide a color key
3. Provide two useful commands within the chimeraX-session:
   1. `scale_color <color this map> <by this value>`    to color one  map by the values of another according to 
      the color key. To re-color according to scale, use `scale_color <map> #2` since the .cxc always defines the 
      scale estimate as `#2`. This is useful after introducing clipping planes.
   2. `occupy_level < level >`  to set the input and output maps on the same level for easy comparison of how 
      modification affected the input map.


## Troubleshooting
### Finding more information 
For brief information regarding input options, please use 
```shell
$ OccuPy --help 
```
For extensive information regarding input options, please use 
```shell
$ OccuPy --help-all 
```
### The modified map is similar to the input map
1. The modification is effected by the power given to `--gamma `, where values larger than 1 mean to modify. Larger 
   values mean to modify more, and typically values between 2 and 10 are useful. 
2. The modification is suppressed if the estimated solvent model decreases confidence in partial occupancies. If 
   there isn't enough solvent for the fitting of the solvent model, it will typically be too wide and prevent 
   modification of lower-scale components. You can check this by using the `--plot` option and inspecting the output.
   You can also use `--solvent-def <mask.mrc>` where the mask is a conventional solvent-mask. This will allow these 
   regions to be omitted during solvent fitting. _This mask does not need to be perfect, and does not limit the 
   modification to areas inside it_. 
### There is a sphere of noise surrounding the amplified map
1. If the confidence is over-estimated, low-scale components will be permitted to be amplified. You can hedge the 
   confidence by using `--hedge-confidence <val>`, where `<val>` is a power, meaning that higher values hedge 
   more. 10 is a reasonable value to try.
2. Another possible reason for the confidence being over-estimated is that the solvent model mean and/or variance is 
   under-estimated. A typical reason for this is that the solvent has been flattened, such that the solvent is not 
   gaussian. `OccuPy` was not designed for this type of reconstruction, since such flattening is typically enforced 
   using a mask which has thus already delineated solvent vs non-solvent. 
3. If the map is not solvent-flattened, and confidence-hedging does not alleviate solvent-amplification surrounding 
   the main map component, use `--solvent-def <mask.mrc>` where the mask is a conventional solvent-mask. This will 
   allow these regions to be omitted during solvent fitting. _This mask does not need to be perfect, and does 
   not limit the modification to areas inside it_. 

