# Make a subtraction mask

<div class="admonition hint">
<p class="admonition-title">Recommendation</p>
<p>
Please read the GUI overview and conduct the intro tutorial first.
</p>
</div>

If you found attenuation or sigmoid modification by local scale useful, you might want to perform signal subtraction 
on your input data so that the subsequent reconstruction will look like the modified output.

<div class="admonition attention">
<p class="admonition-title">Limitation of use</p>
<p>
A subtraction mask is to be used in e.g. RELION. Any other use should be considered at your own risk or unsupported.
</p>
</div>

<div class="admonition attention">
<p class="admonition-title">Subtraction is only remove components</p>
<p>
A subtraction mask can only achieve attenuation of the input data. and because it will be applied uniformly to all 
input data, it is only appropriate for full-occupancy components. Its use is therefore currently limited to e.g. 
detergent regions of membrane proteins and reducing the influence of flexible regions. 
</p>
</div>

---

## 1. Estimate occupancy-mode local scale

1. Open the input map
2. Select occupancy-model local scale just below the modification options
3. Estimate the scale

---

## 2. Set the desired attenuation

1. Activate either the "Attenutate" or "Sigmoid" options in the modification settings and inspect the preview tab of 
   the viewer as you do. 
2. Once happy, click "Modify Map". 
3. Visualize the output by clicking "Launch ChimeraX"
4. Alter the modification until you are happy with the result. 

---

## 3. Generate the subtraction mask

1. Without changing the modification parameters, click "Run->Generate subtraction mask"
2. The output log will report the mask(s) written, which can be opened in e.g. chimeraX. The generated mask(s) will 
   not be opened in the OccuPy GUI. 