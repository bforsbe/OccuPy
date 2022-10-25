# Modify a map 

<div class="admonition attention">
<p class="admonition-title">You need an occupancy estimate</p>
<p>
Please conduct the tutorial to estimate occupancy before this toturial.
You will use the same parameters to modify as accurately as possible
</p>
</div>

---

## 1 Optimize parameters

For fidelity of the modified map (as representing something genuinely possible given the data that was used to make 
the input map) the occupancy should be as accurate as possible. The tutorial on occupancy esstimation guides you to 
do so. In some cases you may just want to achieve a given effect. It's up to you. But determine the scale kernel 
settings you want, and enter them in the GUI, starting from the top down to avoid re-estimation of values you've 
entered. 

---

## 2 Validate the solvent model
<div class="admonition danger">
<p class="admonition-title">No joke</p>
<p>
This is neccessary. Do not skip it. You are not saving time by doing so.
</p>
</div>


---

## 3 Estimate occupancy
Make sure occupancy-mode is selected just below the modification tabs, and click "Estimate scale". This will 
re-estimate and set the occupancy-mode estimate as active.

---

## 3 