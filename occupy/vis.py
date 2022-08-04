from pathlib import Path

import numpy as np
import pylab as plt

def save_fig(
        ori: str,
        extra_specifier: str =None
):
    file_name = 'solModel_' + Path(ori).stem + '.png'
    if extra_specifier is not None:
        file_name = f'solModel_{extra_specifier}_' + Path(ori).stem + '.png'
    plt.savefig(file_name)

def chimx_viz(
        ori: str,
        occ: np.ndarray,
        full: np.ndarray = None,
        threshold_ori: float = None,
        threshold_full: float = None,
        threshold_occ: float = None
):
    file_name = 'chimX_' + Path(ori).stem + '.cxc'

    with open(file_name, 'w') as the_file:

        # -----MODELS --------------------------------------
        print(f'open {ori} ', file=the_file)
        if threshold_ori is not None:
            print(f'vol #1 level {threshold_ori}', file=the_file)

        print(f'open {occ} ', file=the_file)
        if threshold_occ is None:
            print(f'hide #2 ', file=the_file)
        else:
            print(f'vol #2 level {threshold_occ}', file=the_file)

        if full is not None:
            print(f'open {full} ', file=the_file)
            if threshold_full is not None:
                print(f'vol #3 level {threshold_full}', file=the_file)

        # -----COLOR-----------------------------------------
        rainbow = 'rainbow'
        pLDDT_unity = '\'0,red:0.5,orange:0.7,yellow:0.9,cornflowerblue:1.0,blue\''
        pop = '\'0.0,#AAFF00:0.2,#FFAA00:0.4,#FF00AA:0.6,#AA00FF:0.8,#00AAFF\''
        turbo =   '\'0.0,#7a0403:0.1667,#e5460b:0.3333,#faba39:0.5,#a3fd3d:0.6667,#1ae4b6:0.8333,#4686fa:1.0,#30123b\''
        turbo_l = '\'0.0,#d23105:0.1667,#fb8022:0.3333,#edd03a:0.5,#a3fd3d:0.6667,#31f199:0.8333,#29bbec:1.0,#29bbec\''

        clr = turbo_l

        print(f'alias occu_color color sample $1 map $2 palette {clr} range 0.2,1.0 \n', file=the_file)

        print(f'volume #1 color #d3d7cf \n', file=the_file)

        print(f'volume #2 color #A7A7A750 \n', file=the_file)
        print(f'volume #2 style mesh \n', file=the_file)
        print(f'occu_color #1 #2 \n', file=the_file)

        if full is not None:
            print(f'occu_color #3 #2 \n', file=the_file)

        print(f'key {clr} :0.2 :0.333 :0.467 :0.6 :0.733 :0.867 :1.0 size 0.5, 0.04 pos 0.25, 0.08 ticks true tickThickness 2 \n', file=the_file)
        #print(f'hide  #3 \n', file=the_file)

        # ------LIGHTING-------------------------------------
        print(f'lighting soft \n', file=the_file)
        print(f'set bgColor white', file=the_file)
        print(f'camera ortho', file=the_file)

    the_file.close()

