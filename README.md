<img >
   <img width="200" src="resources/logo.png" />
</img>

A fast and simple python module and program to estimate local scaling of cryo-EM maps, to approximate 
occupancy, and optionally also equalise the map according to occupancy while suppressing solvent amplification.

![image](resources/cover.png)


# Estimation of occupancy 
The primary purpose of `OccuPy` is to estimate the local map scale of cryo-EM maps. All regions in a cryo-EM map 
have pixel values that can be considered as drawn from some distribution. In well-resolved regions noise has been 
cancelled such that this distribution contains values above and below solvent. Decreased resolution or occupancy 
conversely results in values that are closer to solvent. `OccuPy` locates a region that exhibits the highest level 
above solvent, and utilizes this to place all other regions on a nominal scale between 0 and 1. This is a proxy for 
occupancy, under the assumption that there is limited flexibility. In maps exhibiting flexibility, the estimated 
map scale does not strictly represent occupancy, as `OccuPy` does not presently separate these factors in map value 
depreciation.

# Amplification of partial occupancies 
`OccuPy` can also amplify confidently estimated partial occupancy (local scale) in the input map by adding the 
`--amplify` or `--attenuate` option. To modify, one must also specify `--beta`, which in simple terms is the power 
of the modification. `--beta 1` means to do nothing, and higher values signify stronger modification. The limiting 
case of amplification is full occupancy at all non-solvent points. The limiting case for attenuation is 0 
occupancy at all point where occupancy was less than 100%.

# Solvent supression 
Map scale amplification by inverse filtering would result in an extremely noisy output if solvent was permitted to 
be amplified. To mitigate this, `OccuPy` estimates a solvent model which limits the amplification of regions where 
the map scale is estimated as near-solvent. One can aid this estimation by providing a mask that covers non-solvent, 
permitting `OccuPy` to better identify solvent. This need not be prcise or accurate, and `OccuPy` will amplify map 
scale outside this region if it is confident about the scale in such a region . This is thus *not* a solvent mask in 
the traditional sense, but rather a solvent definition. Additionally, the estimation of the solvent model does NOT 
affect the estimated map scaling in any way, only the optional amplification.

The supression of solvent is not contigent on amplification - one can choose to supress solvent regions or not, 
irrespective of amplification. This acts as automatic solvent masking, to the extent that  `OccuPy` can reliably 
detect it.

# Expected input 
`OccuPy` expects an input map that has not been solvent-flattened (there should be some solvent somewhere in the map, 
the more the better). `OccuPy` may also work poorly where the map has been post-processed or altered by machine-learning, sharpening, or manual alterations. It has been designed to work in a classification setting, and as such does *not* 
require half-maps, a resolution estimate, or solvent mask. It will likely benefit if you are able to supply these 
things, but does not need it. 

## Installation
`OccuPy` can be installed from the [Python Package Index](https://pypi.org/) (PyPI)

```shell
pip install occupy
```

## Usage

`OccuPy` is a command-line tool 

```shell
$ OccuPy --help

OccuPy: 0.1.4.dev7+g6cc3641.d20220823

$
```

but the tools used within it are available from within a python environment as well

```python
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

The estiamte is based on the relative probability of each voxel value pertaining to non-solvent or solvenr model

:param data:                input array
:param solvent_paramters:   solvent model parameters, gaussian (scale, mean, var)
:param hedge_confidence:    take the estimated confidence to this power to hedge
:param n_lev:               how many levels to use for the histogram
:return:
File:      ~/Documents/Occ/occupy/occupy/occupancy.py
Type:      function

In[3]:

```

# Examples of use 

In its basic form, `OccuPy` simply estimates the map scale, writes it out along with a chimeraX-command script to 
visualise the results easily

```shell
$ OccuPy -i map.mrc 
$ ls  
map.mrc    scale_map.mrc    chimX_map.cxc
```

To modify all confident partial scales regions (local partial occupancy), use `--amplify` and/or  `--attenuate` 
along with `--beta` as described above. Becuase the input is modified and not just estimated, there is now additional 
output map(s). 
```shell
$ OccuPy -i map.mrc  --amplify --beta 4 
$ ls  
map.mrc    scale_map.mrc    attn_4.0_map.mrc    chimX_map.cxc
```

To supress (flatten) solvent content use `--exclude-solvent`
```shell
$ OccuPy -i map.mrc -o no_solvent.mrc --exclude-solvent 
$ ls  
map.mrc    scale_map.mrc    solExcl_map.mrc    chimX_map.cxc


```


