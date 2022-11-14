from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

def save_fig(
        input: str,
        extra_specifier: str =None
):
    file_name = 'solModel_' + Path(input).stem + '.png'
    if extra_specifier is not None:
        file_name = f'solModel_{extra_specifier}_' + Path(input).stem + '.png'
    plt.savefig(file_name,dpi=200)

def chimx_viz(
        input: str,
        scale: str,
        ampl_map: str = None,
        attn_map: str = None,
        sigm_map: str = None,
        solExcl_only_map: str = None,
        threshold_maps: float = None,
        threshold_scale: float = None,
        min_scale: float = 0.2,
        tiles=None,
        silent: bool = False,
        warnings: str = None
):
    ident = Path(input).stem
    if silent:
        ident = f'{ident}_silent'

    file_name = 'chimX_' + ident + '.cxc'

    with open(file_name, 'w') as the_file:

        # -----MODELS --------------------------------------
        print(f'open {input} ', file=the_file)
        if threshold_maps is not None:
            print(f'vol #1 level {threshold_maps}', file=the_file)

        print(f'open {scale} ', file=the_file)
        if threshold_scale is not None:
            print(f'vol #2 level {threshold_scale}', file=the_file)
        print(f'hide #2 ', file=the_file)

        # -----COLOR-----------------------------------------
        rainbow = 'rainbow'
        pLDDT_unity = '\'0,red:0.5,orange:0.7,yellow:0.9,cornflowerblue:1.0,blue\''
        pop = '\'0.0,#AAFF00:0.2,#FFAA00:0.4,#FF00AA:0.6,#AA00FF:0.8,#00AAFF\''
        turbo = '\'0.0,#7a0403:0.1667,#e5460b:0.3333,#faba39:0.5,#a3fd3d:0.6667,#1ae4b6:0.8333,#4686fa:1.0,#30123b\''
        #turbo = ['#d23105', '#fb8022','#edd03a','#a3fd3d','#31f199','#29bbec','#4d6edf']
        turbo = ['#cc3920', '#f0682e','#faab46','#dcdc4b','#a4fa4f','#56f582','#36d7c3','#46a4f6','#4d6edf']
        #turbo = ['#cc3920', '#eb5d2a','#fb923c','#f3c04b','#d1e54a','#a3fa4f','#66f974','#3ae7ab','#38c6da','#4a99fa','#4d6edf']


        n_colors=9
        turbo_l = ''
        labels = key_labels = ''
        vals=np.linspace(0, 1.0, n_colors)
        key_vals = np.linspace(min_scale, 1.0, n_colors)
        for i in np.arange(n_colors):
            turbo_l = f'{turbo_l}{vals[i]:.2f},{turbo[i]}:'
            labels = f'{labels} :{vals[i]:.2f}'
            key_labels = f'{key_labels} :{key_vals[i]:.2f}'
        turbo_l = f'\'{turbo_l[:-1]}\''
        #turbo_l = '\'0.0,#d23105:0.1667,#fb8022:0.3333,#edd03a:0.5,#a3fd3d:0.6667,#31f199:0.8333,#29bbec:1.0,#29bbec\''

        clr = turbo_l

        key_str = f'key {clr} '
        key_str = f'{key_str} {key_labels} size 0.5, 0.04 pos 0.25, 0.08 ticks true tickThickness 2 fontSize 20\n'

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
            if threshold_maps is not None:
                print(f'vol #{c} level {threshold_maps}', file=the_file)
            print(f'hide #{c}', file=the_file)

        if attn_map is not None:
            c += 1
            print(f'open {attn_map} ', file=the_file)
            print(f'scale_color #{c} #2 \n', file=the_file)
            if threshold_maps is not None:
                print(f'vol #{c} level {threshold_maps}', file=the_file)
            print(f'hide #{c}', file=the_file)

        if sigm_map is not None:
            c += 1
            print(f'open {sigm_map} ', file=the_file)
            print(f'scale_color #{c} #2 \n', file=the_file)
            if threshold_maps is not None:
                print(f'vol #{c} level {threshold_maps}', file=the_file)
            print(f'hide #{c}', file=the_file)

        if solExcl_only_map is not None:
            c += 1
            print(f'open {solExcl_only_map} ', file=the_file)
            print(f'scale_color #{c} #2 \n', file=the_file)
            if threshold_maps is not None:
                print(f'vol #{c} level {threshold_maps}', file=the_file)
            print(f'hide #{c}', file=the_file)



        setstr = '#1'
        for i in np.arange(c-2)+3:
            setstr = f'{setstr},{i}'

        print(f'alias occupy_level vol {setstr} level $1 \n',file=the_file)

        output = ampl_map or attn_map

        # Show which tiles are used to define full scale, and which tile is the minimum
        if tiles is not None:
            print(f'alias show_max_tile shape sphere center {tiles[0,0]}, {tiles[0,1]}, {tiles[0,2]} radius {tiles[2,0]}  \n', file=the_file)
            print(f'alias show_min_tile shape sphere center {tiles[1,0]}, {tiles[1,1]}, {tiles[1,2]} radius {tiles[2,0]}  \n', file=the_file)
            print(f'show_max_tile \n', file=the_file)
            c += 1
            print(f'rename  #{c} maxTile id #{c}.1', file=the_file)
            print(f'show_min_tile \n', file=the_file)

            print(f'rename  #{c+1} minTile id #{c}.2', file=the_file)
            print(f'color #{c}.1 #4d6edf54 ', file=the_file)
            print(f'color #{c}.2 #cc392054 ', file=the_file)
            print(f'hide #{c}', file=the_file)

            print(f'rename  #{c} Tiles', file=the_file)
            c += 1

        print(key_str, file=the_file)

        # ------LIGHTING-------------------------------------
        print(f'lighting soft \n', file=the_file)
        print(f'set bgColor white', file=the_file)
        print(f'tool hide log', file=the_file)

        if warnings is not None:
            size = 20
            pos = 'x .05 y .3'
            if silent:
                size = 4
                pos = 'x .05 y .95'
            print(f'2dlab text "{warnings}" color black size {size} {pos} bold true', file=the_file)
            print(f'2dlab text "X" color black size {20*size} x .4 y .3 bold true', file=the_file)

        if silent:
            w = 600
            h = 600
            transparent_bg = False
            supersample = 3

            if output is not None:
                print(f'hide  #1', file=the_file)
            print(f'hide  #2', file=the_file)

            do_transparent=''
            if transparent_bg:
                do_transparent='transparentBackground true'

            print(f'save {ident}_rot1.png supersample {supersample} width {w} height {h} {do_transparent}', file=the_file)
            print(f'turn x 75', file=the_file)
            print(f'turn y 35', file=the_file)
            print(f'view', file=the_file)
            print(f'save {ident}_rot2.png supersample {supersample} width {w} height {h} {do_transparent}', file=the_file)
            print(f'turn x 75', file=the_file)
            print(f'turn y 35', file=the_file)
            print(f'view', file=the_file)
            print(f'save {ident}_rot3.png supersample {supersample} width {w} height {h} {do_transparent}', file=the_file)
            print(f'turn x 75', file=the_file)
            print(f'turn y 35', file=the_file)
            print(f'view', file=the_file)
            print(f'save {ident}_rot4.png supersample {supersample} width {w} height {h} {do_transparent}', file=the_file)
            print(f'exit', file=the_file)

        else:
            print(f'camera ortho', file=the_file)


    the_file.close()

    return file_name

