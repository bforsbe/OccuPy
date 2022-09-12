# OccuPy
A fast and simple python module and program to estimate local scaling of cryo-EM maps, to approximate relative
occupancy and/or resolution, and optionally also equalise the map according to occupancy while suppressing solvent 
amplification.

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
**OccuPy**
- is only applicable to reconstructions produced by averaging, like SPA and STA. That is, *not* for a single tomogram.
- does not sharpen maps. It tries not to.
- does not estimate the _absolute_ local resolution, but to an extent the _relative_ local resolution. See more 
  [here](#the-estimated-scale-looks-like-my-local-resolution). 

## Why estimate local scale?
The local scale contains information about both resolution and occupancy. With this in mind, **OccuPy** is designed to 
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

## Modification of partial occupancies
### Amplification
**OccuPy** can also amplify confidently estimated partial occupancy, which will effectively make weak components 
stronger. To do so, just add `--amplify` and specify a gamma factor to say how much to amplify by. `--gamma 1` means 
to do nothing, and higher values signify stronger amplification. Values higher than about 30 are largely pointless, as 
values in the range 2-5 are typically useful. A *very* high (limiting) value of `--gamma 30` (or more) leads to 
full occupancy at all non-solvent points.
### Attenuation
In some cases you might also want to remove weak components, like in a detergent belt, or to make the distinction to 
full occupancy clearer. You can do this by adding the `--attenuate` option, which uses the same gamma factor. The 
limiting case of very strong attenuation means that all points with weak occupancy are removed. For this reason, 
attenuation tends to use lower `--gamma` values, probably in the range 2-3. Larger values will leave high-scale 
components only.   

### Notes
NOTE  1: You can add both options, and combine it with `--exclude-solvent`. See following section(s) for details.

NOTE  2: `--gamma` values less than 1 are not permitted, as it simply inverts the relationship between amplification 
and attenuation.

NOTE  3: Local scale should only be modified when it approximates occupancy. **OccuPy** will try to remove 
resolution-dependent effects when modification is used, but this relies on appropriate low-pass filtering as 
decribed [here](#the-estimated-scale-looks-like-my-local-resolution).

## Solvent suppression 
Map scale amplification by inverse filtering would result in an extremely noisy output if solvent was permitted to 
be amplified. To mitigate this, **OccuPy** estimates a solvent model which limits the amplification of regions where 
the map scale is estimated as near-solvent. One can aid this estimation by providing a mask that covers non-solvent, 
permitting **OccuPy** to better identify solvent. Usually, this is **not** necessary. **OccuPy** will warn you 
(intently) if it detects that the solvent model may be bad, but it is not guaranteed that it will. You can use the 
option `--plot` to get a figure displaying the solvent model. See also the section on [troubleshooting]
(#troubleshooting). If a solvent mask i needed, it need not be precise or accurate, since **OccuPy** will still be 
able to amplify map scale outside this region if it is confident about it. Thus, a mask supplied to **OccuPy** using 
the option `--solvent-definition` is *not* a solvent mask in the traditional sense, and the estimation 
of the solvent model does NOT affect the estimated map scaling in any way (it only affects the optional scale 
modification and/or solvent suppression).

The suppression of solvent is not contingent on amplification - one can choose to supress solvent regions or not, 
irrespective of scale modification. This acts as automatic solvent masking, to the extent that **OccuPy** can reliably 
detect it.

## Expected input 
**OccuPy** expects an input map that has not been solvent-flattened (there should be some solvent somewhere in the map, 
where more is better). **OccuPy** may also work poorly where the map has been post-processed or altered by 
machine-learning, sharpening, or manual alterations. It has been designed to work in a classification setting, and  
as such does *not* require half-maps, an accurate resolution estimate, or solvent mask. It will likely benefit if you 
are able to supply these things, but does not *need* it. 

## Installation
Regardless if you are using conda or not, **OccuPy** can be installed from the [Python Package Index](https://pypi.
org/project/OccuPy/) (PyPI) using `pip`

```shell
pip install occupy
```
If you are a developer or prefer to download the source code for some other reason, you can also install from 
the cloned repo

```shell
$ git clone https://github.com/bforsbe/OccuPy.git
$ cd occupy 
$ pip install -e . 
```

## Usage

**OccuPy** is a command-line tool 

```shell
$ occupy --version
OccuPy: 0.1.5rc4.dev1+gfa0f2e9.d20220905
```
For development use, you can also import it as a python module.

[//]: # (but the tools and functions are available from within a python environment as well &#40;but this is not intended use )

[//]: # (outside of development&#41;)

[//]: # ()
[//]: # (```shell)

[//]: # (In[1]: import occupy)

[//]: # ()
[//]: # (In[2]: occupy.occupancy.estimate_confidence?                                                                                            )

[//]: # (Signature:)

[//]: # (occupy.occupancy.estimate_confidence&#40;)

[//]: # (    data,)

[//]: # (    solvent_paramters,)

[//]: # (    hedge_confidence=None,)

[//]: # (    n_lev=1000,)

[//]: # (&#41;)

[//]: # (Docstring:)

[//]: # (Estimate the confidence of each voxel, given the data and the solvent model)

[//]: # ()
[//]: # (The estimate is based on the relative probability of each voxel value pertaining to non-solvent or solvenr model)

[//]: # ()
[//]: # (:param data:                input array)

[//]: # (:param solvent_paramters:   solvent model parameters, gaussian &#40;scale, mean, var&#41;)

[//]: # (:param hedge_confidence:    take the estimated confidence to this power to hedge)

[//]: # (:param n_lev:               how many levels to use for the histogram)

[//]: # (:return:)

[//]: # (File:      ~/Documents/Occ/occupy/occupy/occupancy.py)

[//]: # (Type:      function)

[//]: # ()
[//]: # (In[3]:)

[//]: # ()
[//]: # (```)
## Examples of use

### Trying it out 
For easy testing, there is a handy flag to dowload, unzip and use entries from the Electron Microscopy Data Bank (
[EMDB](https://www.ebi.ac.uk/emdb/)). Simply provide the number of the entry to `--emdb` and hang back. Subsequent use 
will not 
re-download the file unless you renamed or moved it.
```shell
$ occupy --emdb 3061             
Fetching emd_3061.map.gz
100% [........................................................................] 21796317 / 21796317
 Done fetching emd_3061.map.gz
Unzipping emd_3061.map.gz
Done unzipping
```
Here are a few entries that might be interesting to test **OccuPy**

| Entry                                         | Sample                         | Box-size |
|-----------------------------------------------|--------------------------------|----------|
| [3061](https://www.ebi.ac.uk/emdb/EMD-3061)   | gamma-secretase                | 180      |
| [30185](https://www.ebi.ac.uk/emdb/EMD-30185) | F-actin                        | 320      |
| [33437](https://www.ebi.ac.uk/emdb/EMD-33437) | RNA polymerase II + nucleosome | 240      |

### Estimating and modifying local map scale 

In its basic form, **OccuPy** simply estimates the map scale, writes it out along with a chimeraX-command script to 
visualise the results easily

```shell
$ occupy -i map.mrc 
$ ls  
map.mrc    scale_res_map.mrc    chimX_map.cxc    log_map.txt
```
The output scale here includes effects due to resolution, and is thus named as such. A log file is written with 
additional details. 

To modify all confident partial scale regions (local partial occupancy), use `--amplify` and/or  `--attenuate` 
along with `--gamma` as described [here](#amplification). Because the input is modified and not just estimated, there is now 
additional 
output map(s). 
```shell
$ occupy -i map.mrc  --amplify --gamma 4 
$ ls  
map.mrc    scale_occ_map.mrc    ampl_4.0_map.mrc    chimX_map.cxc    log_map.txt
```
Because modification was requested, the occupy has tried to remove resolution-dependent factors withing the local 
scale (which should **not** be changed, to make it a better approximation of occupancy (which should be modified). 
Hence, the name of the file reflects this. 

To supress (flatten) solvent content use `--exclude-solvent`
```shell
$ occupy -i map.mrc --exclude-solvent 
$ ls  
map.mrc    scale_res_map.mrc    solExcl_map.mrc    chimX_map.cxc    log_map.txt
```
These can also be combined, of course
```shell
$ occupy -i map.mrc --exclude-solvent --attenuate --amplify --gamma 4
$ ls  
map.mrc    scale_occ_map.mrc    ampl_4.0_solExcl_map.mrc   attn_4.0_solExcl_map.mrc    chimX_map.cxc    log_map.txt
```
## Visualising the local scale
The easiest method of visualizing the estimated local scale is to use the chimeraX command script output by **OccuPy**. 
This will 
1. Color the input (and any output) map by the estimated scale
2. Provide a color key
3. Provide two useful commands within the chimeraX-session:
   1. `scale_color <color this map> <by this value>`    to color one  map by the values of another according to 
      the color key. To re-color according to scale, use `scale_color <map> #2` since the .cxc always defines the 
      scale estimate as `#2`. This is useful after introducing clipping planes.
   2. `occupy_level <level>`  to set the input and output maps on the same level for easy comparison of how 
      modification affected the input map.


## Troubleshooting
### Finding more information 
For brief information regarding input options, please use 
```shell
$ occupy --help 
```
For extensive information regarding input options, please use 
```shell
$ occupy --help-all 
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
### The estimated scale is just 1 everywhere 
1. Well you might have a rock of a complex.
2. If you set the value of `--tau/-t` manually low, then this is the reason. If it got auto-calculated low, you can 
   increase it, but this is a bad idea. It is rather better to increase the `--kernel` so that the value of tau 
   is automatically increased. You may also waent to increase `--lowpass/-lp` ot increase the number of sampled 
   pixel `nv`. You can see what paramters were calculated and used by checking the output log file or using the 
   `--verbose` option. Increasing the kernel size and/or lowpass setting permits more confident sampling of the local 
   scale, but does increase the granularity. Usually a kernel size of 5 or 7 is adequate, with nv-values in the 
   range 30-100. Low-pass defaults to 8 or 3*pixel-size, which ever is larger, but depending on resolution and 
   pixel-size this may be adjusted depending on the sought granularity.  
3. **OccuPy** puts everything on a scale based on what it estimates as "full" through a non-exhaustive search. It 
  is non-exhaustive because it's much faster. If the "full" scale is under-estimated, lots of regions will be 
  "over-full", i.e. over-estimated as full. YOu can reduce the `--tile-size ` from its default value 12 to reduce 
  the area of what defines "full" scale, which will narrow the definition and in general increase the value of full 
  occupancy, thus stretching the range of the estimated scale. For high-resolution maps, a very small tile-size 
  makes the local scale approximate the mass of individual atoms.   
### There is a sphere of noise surrounding the amplified map
4. If the confidence is over-estimated, low-scale components will be permitted to be amplified. You can hedge the 
   confidence by using `--hedge-confidence <val>`, where `<val>` is a power, meaning that higher values hedge 
   more. 10 is a reasonable value to try.
5. Another possible reason for the confidence being over-estimated is that the solvent model mean and/or variance is 
   under-estimated. A typical reason for this is that the solvent has been flattened, such that the solvent is not 
   gaussian. **OccuPy** was not designed for this type of reconstruction, since such flattening is typically enforced 
   using a mask which has thus already delineated solvent vs non-solvent. 
6. If the map is not solvent-flattened, and confidence-hedging does not alleviate solvent-amplification surrounding 
   the main map component, use `--solvent-def <mask.mrc>` where the mask is a conventional solvent-mask. This will 
   allow these regions to be omitted during solvent fitting. _This mask does not need to be perfect, and does 
   not limit the modification to areas inside it_. 

### The estimated scale looks like my local resolution
**OccuPy** estimates the scale. The scale decreases due to **both** lower resolution and lower occupancy. Since it 
is not possible to trivially separate these factors, the current approach to estimate occupancy as separate from 
lower resolution is to low-pass filter the input before estimating the local scale. This is turned on by default 
when amplifying or attenuating the map, to minimize over-amplification of low-scale components that are simply low 
resolution. If one is just estimating scale but wants to reduce resolution-dependent effects, the low-pass 
filtration before scale-estimation can be activated by either --lp-scale or --occupancy. It should then be combined 
with --lowpass/-lp or --resolution/-r to specify the worst resolution among the components for which occupancy is to 
be estimated. For membrane proteins, see [here](#my-membrane-or-detergent-looks-funny).

In the absence of variable occupancy, local scale does actually approximate the local resolution. If you would like 
to include resolution-dependent factors during amplification or attenuation (which is not recommended), you can do 
so by using --raw_scale, which does the opposite of --lp-scale. 

### My membrane or detergent looks funny 
Membranes are lower in resolution due to their amorphous nature which cannot be coherently averaged. Because this 
reduces the local scale, membranes are estimated at low scale. The estimated scale of membranes are thus **not** a 
measure of relative density or occupancy. The low-pass filtration intended to reduce influence of 
resolution-dependent scale factors is only an approximate measure, so that the precise meaning of the local scale of 
membrane and another amorphous regions (as estimated by **OccuPy**) is not well-defined. The lower scale generally 
reflects intuition however, and permits weak attenuation to de-emphasize these regions to make visualization easier.   