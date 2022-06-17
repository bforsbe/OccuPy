from pathlib import Path


def chimx_viz(
        ori,
        full,
        occ,
        threshold_ori=None,
        threshold_full=None,
        threshold_occ=None,
        extra_files=None):
    file_name = 'chimX_' + Path(ori).stem + '.cxc'

    with open(file_name, 'w') as the_file:
        # -----MODELS --------------------------------------
        print(f'open {ori} ', file=the_file)
        if threshold_ori is not None:
            print(f'vol #1 level {threshold_ori}', file=the_file)
        print(f'open {full} ', file=the_file)
        if threshold_full is not None:
            print(f'vol #2 level {threshold_full}', file=the_file)
        print(f'open {occ} ', file=the_file)
        if threshold_occ is None:
            print(f'hide #3 ', file=the_file)
        else:
            print(f'vol #3 level {threshold_occ}', file=the_file)

        # -----COLOR-----------------------------------------
        rainbow = 'rainbow'
        pLDDT_unity = '\'0,red:0.5,orange:0.7,yellow:0.9,cornflowerblue:1.0,blue\''
        pop = '\'0.0,#AAFF00:0.2,#FFAA00:0.4,#FF00AA:0.6,#AA00FF:0.8,#00AAFF\''
        turbo = '\'0.1,#7a0403:0.2,#e5460b:0.3,#faba39:0.5,#a3fd3d:0.7,#1ae4b6:0.8,#4686fa:0.9,#30123b\''
        clr = turbo

        print(f'alias turbo color sample $1 map $2 palette 0.1,#7a0403:0.2,#e5460b:0.3,#faba39:0.5,#a3fd3d:0.7,'
              f'#1ae4b6:0.8,#4686fa:0.9,#30123b range 0.1,1.1 \n', file=the_file)

        print(f'volume #1 color #d3d7cf \n', file=the_file)
        print(f'turbo #1 #3 \n', file=the_file)
        print(f'turbo #2 #3 \n', file=the_file)
        print(f'volume #3 color #A7A7A750 \n', file=the_file)
        print(f'volume #3 style mesh \n', file=the_file)

        print(f'key {clr} :0.1 :0.2 :0.3 :0.5 :0.7 :0.8 :0.9 size 0.5, 0.04 pos 0.25, 0.08 ticks true tickThickness 2 \n', file=the_file)
        #print(f'hide  #3 \n', file=the_file)

        # ------LIGHTING-------------------------------------
        print(f'lighting soft \n', file=the_file)
        print(f'set bgColor white', file=the_file)
        print(f'camera ortho', file=the_file)

    the_file.close()

