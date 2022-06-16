from pathlib import Path


def chimX_viz(
        ori,
        full,
        occ,
        threshold_ori=None,
        threshold_full=None,
        threshold_occ=None,
        extra_files=None):
    file_name = 'chimX_' + Path(ori).stem + '.cxc'

    pLDDT_unity = '0,red:0.5,orange:0.7,yellow:0.9,cornflowerblue:1.0,blue'
    rainbow = 'rainbow'

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
        print(f'volume #1 color #d3d7cf \n', file=the_file)
        print(f'color sample #2 map #3 palette {rainbow} range 0,1 \n', file=the_file)
        print(f'volume  #3 color #4077bf40 \n', file=the_file)

        # ------LIGHTING-------------------------------------
        print(f'lighting soft \n', file=the_file)
        print(f'set bgColor white', file=the_file)
        print(f'camera ortho', file=the_file)

    the_file.close()

