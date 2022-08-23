from pathlib import Path

import numpy as np
import pylab as plt

def save_fig(
        input: str,
        extra_specifier: str =None
):
    file_name = 'solModel_' + Path(input).stem + '.png'
    if extra_specifier is not None:
        file_name = f'solModel_{extra_specifier}_' + Path(input).stem + '.png'
    plt.savefig(file_name)

def chimx_viz(
        input: str,
        scale: str,
        ampl_map: str = None,
        attn_map: str = None,
        threshold_input: float = None,
        threshold_scale: float = None,
        threshold_ampl: float = None,
        threshold_attn: float = None,
        min_scale: float = 0.2,
        silent: bool = False
):
    ident = Path(input).stem
    if silent:
        ident = f'{ident}_silent'

    file_name = 'chimX_' + ident + '.cxc'

    with open(file_name, 'w') as the_file:

        # -----MODELS --------------------------------------
        print(f'open {input} ', file=the_file)
        if threshold_input is not None:
            print(f'vol #1 level {threshold_input}', file=the_file)

        print(f'open {scale} ', file=the_file)
        if threshold_scale is not None:
            print(f'vol #2 level {threshold_scale}', file=the_file)
        print(f'hide #2 ', file=the_file)

        # -----COLOR-----------------------------------------
        rainbow = 'rainbow'
        pLDDT_unity = '\'0,red:0.5,orange:0.7,yellow:0.9,cornflowerblue:1.0,blue\''
        pop = '\'0.0,#AAFF00:0.2,#FFAA00:0.4,#FF00AA:0.6,#AA00FF:0.8,#00AAFF\''
        turbo = '\'0.0,#7a0403:0.1667,#e5460b:0.3333,#faba39:0.5,#a3fd3d:0.6667,#1ae4b6:0.8333,#4686fa:1.0,#30123b\''
        turbo = ['#d23105', '#fb8022','#edd03a','#a3fd3d','#31f199','#29bbec','#29bbec']


        n_colors=7
        turbo_l = ''
        labels = ''
        vals=np.linspace(min_scale, 1.0, n_colors)
        for i in np.arange(n_colors):
            turbo_l = f'{turbo_l}{vals[i]:.2f},{turbo[i]}:'
            labels = f'{labels} :{vals[i]:.2f}'
        turbo_l = f'\'{turbo_l[:-1]}\''
        #turbo_l = '\'0.0,#d23105:0.1667,#fb8022:0.3333,#edd03a:0.5,#a3fd3d:0.6667,#31f199:0.8333,#29bbec:1.0,#29bbec\''

        clr = turbo_l

        key_str = f'key {clr} '
        key_str = f'{key_str} {labels} size 0.5, 0.04 pos 0.25, 0.08 ticks true tickThickness 2 \n'

        print(f'alias scale_color color sample $1 map $2 palette {clr} range {min_scale},1.0 \n', file=the_file)

        print(f'alias set_scale_color_range color sample $1 map $2 palette {clr} range {min_scale},1.0 \n', file=the_file)

        print(f'volume #1 color #d3d7cf \n', file=the_file)

        print(f'volume #2 color #A7A7A750 \n', file=the_file)
        print(f'volume #2 style mesh \n', file=the_file)
        print(f'scale_color #1 #2 \n', file=the_file)

        c = 2

        if ampl_map is not None:
            c += 1
            print(f'open {ampl_map} ', file=the_file)
            print(f'scale_color #{c} #2 \n', file=the_file)
            if threshold_ampl is not None:
                print(f'vol #{c} level {threshold_ampl}', file=the_file)

        if attn_map is not None:
            c += 1
            print(f'open {attn_map} ', file=the_file)
            print(f'scale_color #{c} #2 \n', file=the_file)
            if threshold_attn is not None:
                print(f'vol #{c} level {threshold_attn}', file=the_file)

        setstr = '#1'
        for i in np.arange(c-2)+3:
            setstr = f'{setstr},{i}'

        print(f'alias occupy_level vol {setstr} level $1 \n',file=the_file)

        output = ampl_map or attn_map

        print(key_str, file=the_file)

        # ------LIGHTING-------------------------------------
        print(f'lighting soft \n', file=the_file)
        print(f'set bgColor white', file=the_file)
        if silent:
            w = 600
            h = 600
            if output is not None:
                print(f'hide  #1', file=the_file)
            print(f'hide  #2', file=the_file)

            print(f'save {ident}_rot1.png supersample 3 width {w} height {h} transparentBackground true', file=the_file)
            print(f'turn x 75', file=the_file)
            print(f'turn y 35', file=the_file)
            print(f'save {ident}_rot2.png supersample 3 width {w} height {h} transparentBackground true', file=the_file)
            print(f'turn x 75', file=the_file)
            print(f'turn y 35', file=the_file)
            print(f'save {ident}_rot3.png supersample 3 width {w} height {h} transparentBackground true', file=the_file)
            print(f'turn x 75', file=the_file)
            print(f'turn y 35', file=the_file)
            print(f'save {ident}_rot4.png supersample 3 width {w} height {h} transparentBackground true', file=the_file)
            print(f'exit', file=the_file)

        else:
            print(f'camera ortho', file=the_file)

    the_file.close()

