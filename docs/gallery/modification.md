# Proteasome 14085 

Versions: 
```
OccuPy 1.8.0rc2
ChimeraX 1.4 (2022-06-03)
```

## In OccuPy

1. Fetch EMDB 14085. This may take a minute, as the map is 384px.
2. Set scale mode = occupancy
3. Click "Estimate scale" 
4. Enable amplification and set Power=30
5. Enable Attenuation and set Power=2
6. Enable Sigmoid and set Power=5 and Pivot=0.22
7. Click "Modify Map"
8. Launch ChimeraX (open chimX_emd_14085.cxc through ChimeraX)

## In chimeraX

For comparing input (#1) and amplified (#3)
```commandline
hide 
show #1  
view matrix camera -0.99855,-0.042865,-0.032681,212.84,0.053661,-0.73359,-0.67747,-405.78,0.005068,-0.67824,0.73482,1015.9
occupy_level 11
show #3
```

<div class="c-compare" style="--value:20%;">
  <img class="c-compare__left" src="https://drive.google.com/uc?export=view&id=1g4D7AUyeZXfROoukWvzAkdQoZ6Fvnf1z" alt="Input" />
  <img class="c-compare__right" src="https://drive.google.com/uc?export=view&id=1pRrOUqs0EiJXvQGC3saxbbG66VhV7XAZ" alt="Amplified" />
  <input type="range" class="c-rng c-compare__range" min="0" max="100" value="20" oninput="this.parentNode.style.
setProperty('--value', `${this.value}%`)" />
</div>


For comparing input (#1) and attenuated (#4)
```commandline
hide 
show #1  
view matrix camera 0.064209,-0.9974,-0.032681,143.71,0.73227,0.06934,-0.67747,-399.85,0.67798,0.019568,0.73482,1018.3
occupy_level 7
show #4
```

<div class="c-compare" style="--value:20%;">
  <img class="c-compare__left" src="https://drive.google.com/uc?export=view&id=1Fk7jg2dkRzQ133XJ-x_FTaOEgQe_xJ2V" alt="Input" />
  <img class="c-compare__right" src="https://drive.google.com/uc?export=view&id=1XETOdONDIepffDYYNNg2WXEuPz4Tv7FX" alt="Attenuation" />
  <input type="range" class="c-rng c-compare__range" min="0" max="100" value="20" oninput="this.parentNode.style.
setProperty('--value', `${this.value}%`)" />
</div>

For comparing input (#1) and sigmoid (#5)
```commandline
hide 
show #1  
view matrix camera 0.064209,-0.9974,-0.032681,143.71,0.73227,0.06934,-0.67747,-399.85,0.67798,0.019568,0.73482,1018.3
occupy_level 10
show #5
```

<div class="c-compare" style="--value:20%;">
  <img class="c-compare__left" src="https://drive.google.com/uc?export=view&id=1R6nveLCd1cnjrglXIh4Chd6vvRV6F7qq" alt="Input" />
  <img class="c-compare__right" src="https://drive.google.com/uc?export=view&id=19h52QHCc5gIAUffw8bngUOiyTYdqyT0E" alt="Sigmoid" />
  <input type="range" class="c-rng c-compare__range" min="0" max="100" value="20" oninput="this.parentNode.style.
setProperty('--value', `${this.value}%`)" />
</div>




