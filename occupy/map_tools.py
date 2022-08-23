import mrcfile.mrcfile
import numpy as np
import mrcfile as mf
import scipy as sp
from pathlib import Path

from scipy import fft as spfft

from pkg_resources import get_distribution

__version__ = get_distribution("occupy").version


def create_radial_mask(
        size: int,
        dim: int,
        center: int = None,
        radius: float = None
):
    """
    Create a circular or spherical dimensional mask or kernel

    :param size:    Output array length
    :param dim:     Output array dimension
    :param center:  Center of the radial region
    :param radius:  Radius of the radial region
    :return:        Boolean array
    """

    assert dim == 2 or dim == 3

    # use the middle of the image unless otherwise specified
    if center is None:
        center = (size - 1) / 2

    # use the output size diameter unless otherwise specified
    if radius is None:
        radius = center

    # Ensure lower precision
    center = np.float32(center)
    radius = np.float32(radius)

    if dim == 2:

        # _ix is equivalent to x, y = np.ogrid[:s, :s] but permits specifying dtype
        x, y = np.ix_(np.arange(size, dtype=np.int32), np.arange(size, dtype=np.int32))

        dist_from_center = (x - center) ** 2 + (y - center) ** 2

        dist_from_center = np.sqrt(dist_from_center)

    else:

        #  _ix is equivalent to x, y, z = np.ogrid[:s, :s, :s] but permits specifying dtype
        x, y, z = np.ix_(np.arange(size, dtype=np.int32), np.arange(size, dtype=np.int32),
                         np.arange(size, dtype=np.int32))

        dist_from_center = (x - center) ** 2 + (y - center) ** 2 + (z - center) ** 2

        dist_from_center = np.sqrt(dist_from_center.astype(np.float32))

    out = (dist_from_center <= radius)

    return out

def new_mrc(
        data: np.ndarray,
        file_name: str,
        parent: str = None,
        vox_sz: int = None,
        verbose: bool = False,
        extra_header=None,
        log=None
):
    """
    Write data to a new mrc file, and optionally an existing (parent) file to define data parameters

    If the parent has different dimensions, the box size is assumed equal with unequal sampling.
    The voxel-size and any offset is thus adjusted so that the maps coincide.

    :param data:            Data to write
    :param file_name:       Output file name
    :param parent:          Parent file name            (optional)
    :param vox_sz:          Output voxel size           (optional)
    :param verbose:         Be verbose                  (optional)
    :param extra_header:    String for output header    (optional)
    :param log:             Log-file name               (optional)
    :return:
    """

    if parent is None and vox_sz is None:
        raise ValueError('No parent or pixel-value provided for new mrc file')

    offset = 0
    factor = 1

    # Make sure the suffix is .mrc
    file_name = f'{Path(file_name).stem}.mrc'

    # Open
    o_file = mf.new(file_name, overwrite=True)

    # set_data() will update header info and stats
    o_file.set_data(data.astype(np.float32))

    # Add labels to document what happened
    # TODO put back in once mrcfile is version > 1.4.2
    #o_file.add_label(f'Created using OccuPy {__version__}')
    #o_file.add_label(f'{extra_header}')

    adjust_to_parent(parent,file_handle=o_file)

    o_file.flush()
    o_file.validate()
    o_file.close()

    if verbose:
        if log is None:
            print(f'Wrote new file {file_name}')
        else:
            print(f'Wrote {file_name}', file=log)


def adjust_to_parent(
        parent: str =None,
        file_name: str = None,
        file_handle: mf.mrcfile.MrcFile = None
):
    """
    Adjust an mrc-file to coincide with the parent, i.e. overlap their boxes by adjusting voxel-size and offset

    :param parent:        Parent file name
    :param file_name:     File name of the mrc-file to adjust
    :param file_handle:   File-handle of the mrc-file to adjust
    :return:

    """
    if parent is None:
        return

    # Do not close file by default
    close = False

    # Open file if necessary
    if file_handle is None:
        assert file_name is not None

        # If open, then close
        close = True

        file_handle = mf.open(file_name,'r+')

    parent_handle = mf.open(parent)

    # Relative scaling
    factor = parent_handle.header['nx'] / file_handle.header['nx']

    # Map centering
    offset_p = parent_handle.header['nxstart']

    # Map scaling
    pix_size_p = parent_handle.voxel_size.x

    # Adjust
    file_handle.voxel_size = pix_size_p * factor
    file_handle.nstart = int(round(offset_p / factor))

    # Flush to be sure
    file_handle.flush()

    # Close if necessary
    parent_handle.close()
    if close:
        file_handle.close()



def change_voxel_size(
        file: str,
        sz: int = None,
        parent: str = None
):
    if (parent is None) and (sz is None):
        raise ValueError('Change to pixel size to what? (No parent or value provided)')

    f_mod = mf.open(file, 'r+')
    if parent is not None:
        try:
            f_ref = mf.open(parent)
            f_mod.voxel_size = f_ref.voxel_size
            f_ref.close()
        except ValueError:
            print('Could not open parent file for reading pixel size')
    elif sz is not None:
        f_mod.voxel_size = sz
    f_mod.flush()
    f_mod.close()


def clip_to_range(
        change: np.ndarray,
        reference: np.ndarray
):
    """
    Clip an array to have the range as a reference array

    :param change:          array to clip
    :param reference:       array to define range

    :return:                clipped array
    """
    rp = np.array([np.min(reference), np.max(reference)])

    change = np.clip(change, rp[0], rp[1])

    return change


def uniscale_map(
        data: np.ndarray,
        move: bool = False
):
    """
    Rescale an array to have a range of 1, and optionally to move it to lie on [0,1]

    :param data:    input array
    :param norm:    move to [0,1]?
    :return:        rescaled array

    """
    param = [np.min(data), np.max(data)]
    data /= param[1] - param[0]
    if move:
        data -= np.min(data)
    return data


def lowpass(
        in_data: np.ndarray,
        resolution: float = None,
        voxel_size: float = None,
        output_size: int = None,
        square: bool = False,
        resample: bool = False
):
    """
    Low-pass a 2D- or 3D-array. Intended for cryo-EM reconstructions. 
    
    Will place a radial or square window and omit high-frequency conponents outside this window. 
    If resampling, the output box will be changed to crop or pad the input. 
    
    One must specify either 
        1) The desired output size (implies rescale) 
        2) The cutoff frequency (resolution) AND pixel size.  
    
    :param in_data:         input array to be low-passed
    :param resolution:      spatial cutoff [Å]
    :param output_size:     output array size [pix]
    :param voxel_size:      input voxel size [Å]
    :param square:          use a square (not radial) window
    :param resample:        allow output to be cropped/padded
    
    :return:                low-passed array
    """

    # Test square
    n = np.shape(in_data)
    assert len(np.unique(np.shape(n))) == 1, "Input array to lowpass is not square"

    # Test dim
    ndim = len(n)
    assert ndim == 2 or ndim == 3, "Input array to lowpass is not 2 or 3 "

    # Test even
    n = n[0]
    assert n % 2 == 0, "Input array size is not even"

    # Test required input
    assert output_size is not None or voxel_size is not None, "Lowpass needs pixel size or number of pixels."
    assert output_size is not None or resolution is not None, "Lowpass needs a cutoff resolution or number of pixels"

    out_voxel_size = None
    # If the output size is specified, then we are resampling
    if output_size is not None:
        keep_shells = int(output_size / 2)
        resample = True
    # Otherwise the voxel size must have been specified
    else:
        keep_shells = int(np.floor((n * voxel_size) / resolution))  # Keep this many of the lower frequencies
        out_voxel_size = np.copy(voxel_size)

    # Normalization factor for unequal input/output
    factor = 1
    if resample:
        factor = output_size / n

    # FFT forward
    f_data = spfft.rfftn(in_data)  # *2*np.pi/n
    f_data = sp.fft.fftshift(f_data, axes=(0, 1))

    # If we are resampling, then we may be able to provide the output voxel size
    if resample and voxel_size is not None:
        out_voxel_size = voxel_size * n / (2 * keep_shells)

    # We are going to grab central information from the input and make it central in the output
    mid_in = int(n / 2)
    mid_out = None

    if 2 * keep_shells > n:
        # Pad instead
        if not resample:
            # Padding without resampling is not possible
            return in_data
        t = np.zeros((2 * keep_shells, 2 * keep_shells, keep_shells + 1), dtype=np.complex64)
        edge = int((2 * keep_shells - n) / 2)
        t[edge:edge + n, edge:edge + n, :-edge] = f_data

    if resample:
        mid_out = keep_shells
        t = np.zeros((2 * keep_shells * np.ones(ndim).astype(int)), dtype=np.complex64)
        t = t[..., keep_shells - 1:]
    else:
        mid_out = mid_in
        t = np.zeros(np.shape(f_data), dtype=np.complex64)

    keep_shells = int(np.min([keep_shells, n / 2]))
    if ndim == 3:
        t[mid_out - keep_shells:mid_out + keep_shells, mid_out - keep_shells:mid_out + keep_shells, :keep_shells + 1] = \
            f_data[mid_in - keep_shells:mid_in + keep_shells, mid_in - keep_shells:mid_in + keep_shells,
            :keep_shells + 1]
    elif ndim == 2:
        t[mid_out - keep_shells:mid_out + keep_shells, :keep_shells + 1] = \
            f_data[mid_in - keep_shells:mid_in + keep_shells, :keep_shells + 1]

    if not square:
        mask = create_radial_mask(2 * mid_out, radius=keep_shells + 1, dim=ndim)[..., mid_out - 1:]
        t = np.multiply(t, mask)

    f_data2 = np.fft.ifftshift(t, axes=(0, 1))
    out_data = spfft.irfftn(f_data2)

    # The FFT must be normalized
    if resample:
        out_data *= factor ** ndim

    return out_data, out_voxel_size


def lowpass_map(
        data: np.ndarray,
        cutoff: float = None,
        voxel_size: float = 1.0,
        resample: bool = False,
        keep_scale: bool = False
):
    if cutoff is None:
        return data

    n = np.shape(data)[0]
    ndim = len(np.shape(data))
    ref_scale = np.max(data)
    assert ndim == 3  # TODO make work for 2D just in case

    f_data = np.fft.rfftn(data)
    f_data = np.fft.fftshift(f_data, axes=(0, 1))

    cutoff /= voxel_size
    cutoff_level = int(np.floor(2 * (n / cutoff)))  # Keep this many of the lower frequencies
    mid = int(n / 2)

    if resample:  # TODO test/fix
        mid_resample = cutoff_level // 2
        mask = create_radial_mask(cutoff_level, ndim)[:, :, mid_resample:]
        t = f_data[mid - cutoff_level:mid + cutoff_level, mid - cutoff_level:mid + cutoff_level, :cutoff_level + 1]
        # print(t.shape,mask.shape)
        t = np.multiply(t, mask)
    else:
        mask = create_radial_mask(n, ndim, radius=cutoff_level)[:, :, mid - 1:]
        # print(f_data.shape,mask.shape,mask.sum(),mask.size,n,cutoff_level)
        t = np.multiply(f_data, mask)

    f_data = np.fft.ifftshift(t, axes=(0, 1))
    r_data = np.fft.irfftn(f_data)
    if keep_scale:
        m = np.mean(r_data)
        r_data = (r_data - m) * (ref_scale / np.max(r_data)) + m
    return r_data
