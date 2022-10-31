# Other
This section contains help on common concerns and questions. Further help and insight is offered through the issue 
tracker. 

## Command-line help 
For brief information regarding input options on the command line, please use 
```shell
$ occupy --help 
```
For extensive information regarding input options, see the GUI overview tutorial.


## The modified map is similar to the input map
1. The modification is effected by the power you choose, where values larger than 1 mean to modify. Larger 
   values mean to modify more, and typically values between 2 and 10 are useful. Try increasing it. 
2. Check your solvent model (tab next to output log). The modification is suppressed if the estimated solvent model 
   is very wide, which decreases confidence in partial occupancies. If 
3. 
   there isn't enough solvent for the fitting of the solvent model, it will typically be too wide and prevent 
   modification of lower-scale components. You can check this by using the `--plot` option and inspecting the output.
   You can also use `--solvent-def <mask.mrc>` where the mask is a conventional solvent-mask. This will allow these 
   regions to be omitted during solvent fitting. _This mask does not need to be perfect, and does not limit the 
   modification to areas inside it_. 
## The estimated scale is just 1 everywhere 
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
## There is a sphere of noise surrounding the amplified map
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

## The estimated scale looks like my local resolution
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

## My membrane or detergent looks funny 
Membranes are lower in resolution due to their amorphous nature which cannot be coherently averaged. Because this 
reduces the local scale, membranes are estimated at low scale. The estimated scale of membranes are thus **not** a 
measure of relative density or occupancy. The low-pass filtration intended to reduce influence of 
resolution-dependent scale factors is only an approximate measure, so that the precise meaning of the local scale of 
membrane and another amorphous regions (as estimated by **OccuPy**) is not well-defined. The lower scale generally 
reflects intuition however, and permits weak attenuation to de-emphasize these regions to make visualization easier. 



