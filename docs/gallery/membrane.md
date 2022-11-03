# GluK2/K5 kainate receptor 23015

Versions: 
```
OccuPy 1.8.0rc2
ChimeraX 1.4 (2022-06-03)
```

## In OccuPy

1. Fetch EMDB 23015.
2. Set the input lowpass to 5Å. This is too low to provide a reasonable occupancy estimate, but it's the value used 
   in the paper to show modification when occupancy is under-estimated. A better value for fidelity is probably 
   around 10Å. 
3. Set scale mode = occupancy
4. Click "Estimate scale" 
5. Enable Amplification and set Power=3
6. Enable Attenuation and set Power=3
7. Enable Sigmoid and set Power=30 and Pivot=0.50
8. Click "Modify Map"
9. Launch ChimeraX (open chimX_emd_23015.cxc through ChimeraX)

## In chimeraX
Use the command `occupy_level <value>` to set the input and all modifies maps at the same threshold value. 
```commandline
view matrix camera 1.4173e-16,-4.3526e-16,-1,-289.68,0.99756,0.069756,1.1102e-16,164.34,0.069756,-0.99756,4.4409e-16,199.43
occupy_level 0.65
```

<div class="c-compare" style="--value:25%; --w:16; --h:5.9;">
  <img class="c-compare__left" src="https://drive.google.com/uc?export=view&id=1UoLxteGSdJy41iaam88mAKJQ178FUCf4" 
alt="level 0.65" />
  <img class="c-compare__right" src="https://drive.google.com/uc?export=view&id=1OC8Rnba3PaWSEeY77yE3dExJYiywSGMi" 
alt="level 0.30" />
  <input type="range" class="c-rng c-compare__range" min="0" max="100" value="25" oninput="this.parentNode.style.
setProperty('--value', `${this.value}%`)" />
</div>
