# Malate dehydrogenase 

Versions: 
```
OccuPy 1.7.0
ChimeraX 1.4 (2022-06-03)
Gemmi 0.5.6
Relion 4.0-beta-2-commit-c3ddd0
```
## Alter occupancy of pdb model
Altered occupancy of one pdb model chain, generate theoretical density and estimate occupancy of the density using 
OccuPp
![image](https://drive.google.com/uc?export=view&id=1ZIJ7vKye1BXBjIPclJs8YbrR74W1VKQu)


# Setup
Use a bash terminal to make a tamplate for occupancy and b-factor modification.

## Get and prep files 
```commandline
wget https://files.rcsb.org/download/1UXI.pdb
sed -n '/^ATOM/q;p' 1UXI_noWater.pdb > header.pdb
grep ^ATOM 1UXI_noWater.pdb | grep " A " > chain_A.pdb
grep ^ATOM 1UXI_noWater.pdb | grep " B " > chain_B.pdb
grep ^HETATM 1UXI_noWater.pdb > chain_NAD_FUM.pdb
```

To alter the occupancy (to 40%) of atoms in chain A of the model:
```bash
cat header.pdb > 1UXI_occ_template.pdb
sed 's/^\(.\{57\}\).\{4\}/\1xOc /' chain_A.pdb >> 1UXI_occ_template.pdb
echo "TER" >> 1UXI_occ_template.pdb
cat chain_B.pdb >> 1UXI_occ_template.pdb
echo "TER" >> 1UXI_occ_template.pdb
cat chain_NAD_FUM.pdb >> 1UXI_occ_template.pdb
echo "END" >> 1UXI_occ_template.pdb
```
Generate the density using gemmi, and format it using relion
```commandline
sed 's/1xOc/0.40/g' 1UXI_occ_template.pdb > 1UXI_occ_0.40.pdb
~/install/gemmi/gemmi sfcalc --dmin=10  1UXI_occ_0.40.pdb --write-map=raw.mrc --for=electron --unknown=O --rate 3 > log.txt
relion_image_handler --new_box 100 --i raw.mrc --o cube.mrc --shift_x -5 --shift_y -5 --shift_z -15
relion_image_handler --i cube.mrc --o equal.mrc --rescale_angpix 1.66
relion_image_handler --i equal.mrc --lowpass 4 --o 1UXI_occ0.40_LP4.mrc
```
Estimate scale and amplify, and open in chimera
```commandline
occupy -i 1UXI_occ0.40_LP4.mrc --occupancy -am 30 --show-chimerax
chimerax chimX_1UXI_occ0.40_LP4.cxc 1UXI_occ_0.40.pdb
```
In chimeraX, the input pdb with altered occupancies should be opened as #6. 
```commandline
fitmap #6 inMap #3
molmap #6 20
volume #7 level 0.0545
volume mask #3 surfaces #7
scale_color #8 #2
hide #1
hide #6 models
hide #7
```



## Alter B-factors of pdb model
To alter B-factors (to 200Å) of the chain A of the model instead of occupancy:
![image](https://drive.google.com/uc?export=view&id=1lnzmjYM_fZ5W8paQOEm_GKip5hVlrdBX)


```commandline
cat header.pdb > 1UXI_bfac_template.pdb
sed 's/^\(.\{62\}\).\{5\}/\1xBfa /' chain_A.pdb >> 1UXI_bfac_template.pdb
echo "TER" >> 1UXI_bfac_template.pdb
cat chain_B.pdb >> 1UXI_bfac_template.pdb
echo "TER" >> 1UXI_bfac_template.pdb
cat chain_NAD_FUM.pdb >> 1UXI_bfac_template.pdb
echo "END" >> 1UXI_bfac_template.pdb
```
Generate the pdb-file with altered b-factors, to be used as uinput to gemmi
```commandline
sed 's/1Bfac/200.0/g' 1UXI_bfac_template.pdb > 1UXI_bfac_200.pdb
```
After this point, use the same procedure as described above for occupancy