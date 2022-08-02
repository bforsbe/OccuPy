# OccuPy 

A fast and simple python module and program to estimate local scaling of cryo-EM maps, to approximate 
occupancy, and optionally also equalise the map according to occupancy while suppressing solvent amplification.

![image](resources/cover.png)


# Estimation of occupancy 
The primary purpose of OccuPy is to estimate the local map scale of cryo-EM maps. 
All regions in a cryo-EM map 
have pixel values that can be considered as drawn from some distribution. 
In well-resolved regions this distribution contains values above and below solvent.
Decreased resolution or occupancy results in values that are closer to solvent. 
OccuPy locates a region that exhibits the highest level above solvent, 
and utilizes this to place all other regions on a nominal scale between 0 and 1. 
This is a proxy for occupancy, under the assumption that there is limited flexibility. 
In Maps exhibiting flexibility, the estimated map scale does not strictly represent occupancy, 
as OccuPy does not deconvolute these factors in map value depreciation. 

# Occupancy Equalisation with solvent supression
OccuPy also attempts to equalise the input map according to occupancy, such that all regions are on the same nominal 
scale (100%). 
However, this type of inverse filtering would result in an extremely noisy output due to e.g. solvent 
amplification, where the estimated occupancy is typically very low. 
OccuPy therefore attempts to supress solvent amplification.  
A single gaussian if fit to the solvent peak of the input map histogram, producing a solvent model. 
Optionally, one can supply a mask to delinate a region that will constitute a solvent definition, to aid this fitting.
Inverse filtering utilizes the solvent model to estimate the confidence that each pixel represents solvent, and 
limits occupancy equalization according to this. 
The estimation of the solvent model NOT affect the estimated map scaling (occupancy), and a threshold occupancy 
can manually be specified, below which inverse filtering is not performed.

# Requirements
OccuPy requires an input map that has not been solvent-flattened (there should be some solvent somewhere in the map, 
the more the better). In may also work poorly where the map has been post-processed or altered by machine-learning, 
sharpening, or manual alterations. It has been designed to work in a classification setting, and as such does *not* 
require half-maps, a resolution estimate, or solvent mask. It can benefit from these things, but does not need it. 



