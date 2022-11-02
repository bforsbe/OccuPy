# Apoferritin 11638 

Versions: 
```
OccuPy 1.7.0
ChimeraX 1.4 (2022-06-03)
```
![image](https://drive.google.com/uc?export=view&id=1JqWtouDZuVFD9HVqbCiraCxrDDo5Kz_C)
# Setup
Get the PDB for annotation
```commandline
$ wget https://files.rcsb.org/download/7A4M.pdb
```

## In OccuPy

1. Fetch EMDB 11638
2. Set extra option "Naive normalization" = checked
3. Estimate scale 
4. Launch ChimeraX (open chimX_emd_11638.cxc through ChimeraX)

## In chimeraX
Open 7A4M.pdb, here as #4
```commandline
hide cartoon
hide atoms
select #4:95-104,48-58
show sel 
view sel
molmap sel 8
vol #5 level 0.113
vol mask #1 surfaces #5 
vol gaussian #6 sdev 0.5 
hide #5 
volume #7 color #00000099
scale_color #7 #2 
select H 
hide sel
surface dust #6 size 2
color #4 #bababa transparency 0
color byhetero
graphics silhouettes true
```
## Other Views
### Waters 
![image](https://drive.google.com/uc?export=view&id=1QpIHuV5keCZLflykUYZLBohWao1WRU-F)
## In OccuPy

1. Set extra option "Naive normalization" = **unchecked**
2. Set input lowpass = 3Å
3. Set scale_mode = occupancy
4. Estimate scale 
5. Set sigmoid power = 30 , pivot = 0.05 
6. Modify map
7. Launch ChimeraX (open chimX_emd_11638.cxc through ChimeraX)