import numpy as np
import mrcfile as mf
import scipy as sp

from scipy import fft as spfft

__version__ = "0.1.3"


def create_circular_mask(
        s: int,
        dim: int,
        soft: bool = False,
        center: int = None,
        radius: float = None
):
    if center is None:  # use the middle of the image
        center = (s - 1) / 2

    if radius is None:
        radius = center

    #if s % 2 == 0:
    #    center += 0.5
    #    radius += 0.5

    center = np.float32(center)
    radius = np.float32(radius)

    if dim == 2:
        # x, y = np.ogrid[:s, :s]
        x, y = np.ix_(np.arange(s, dtype=np.int32), np.arange(s, dtype=np.int32))
        dist_from_center = np.sqrt((x - center) ** 2 + (y - center) ** 2)
    elif dim == 3:
        # x, y, z = np.ogrid[:s, :s, :s]
        x, y, z = np.ix_(np.arange(s, dtype=np.int32), np.arange(s, dtype=np.int32), np.arange(s, dtype=np.int32))
        dist_from_center = (x - center) ** 2 + (y - center) ** 2 + (z - center) ** 2
        dist_from_center = np.sqrt(dist_from_center.astype(np.float32))
    else:
        raise ValueError('Mask dimension is not 2 or 3 ')

    if soft:  # TODO fix
        raise ValueError('Ah, poor implementation, do not use soft circular mask right now.')
        dist_from_center = np.divide(dist_from_center <= radius, dist_from_center, where=dist_from_center != 0)

    mask = (dist_from_center <= radius)
    return mask


def mask_sphere(
        input_data: np.ndarray,
        soft: bool = False,
        center: int = None,
        radius: int = None
):
    dim = len(input_data.shape)
    n = input_data.shape[0]

    if center is None:  # use the middle of the image
        center = int(n / 2)

    if radius is None:
        radius = center

    if n % 2 == 0:
        center -= 0.5
        radius -= 0.5

    if dim == 2:
        x, y = np.ogrid[:n, :n]
        dist_from_center = np.sqrt((x - center) ** 2 + (y - center) ** 2)
    elif dim == 3:
        x, y, z = np.ogrid[:n, :n, :n]
        dist_from_center = np.sqrt((x - center) ** 2 + (y - center) ** 2 + (z - center) ** 2)
    else:
        raise ValueError('Mask dimension is not 2 or 3 ')

    if soft:  # TODO fix
        raise ValueError('Ah, poor implementation, do not use soft circular mask right now.')
        dist_from_center = np.divide(dist_from_center <= radius, dist_from_center, where=dist_from_center != 0)

    return input_data[(dist_from_center <= radius)]


def new_mrc(
        data: np.ndarray,
        file_name: str,
        parent: str = None,
        sz: int = None,
        verbose: bool = False,
        extra_header = None,
        log=None
):
    offset = 0
    factor = 1

    o_file = mf.new(file_name, overwrite=True)
    o_file.set_data(data.astype(np.float32))

    if parent is not None:
        p = mf.open(parent)
        offset = p.header['nxstart']
        pix_size = p.voxel_size.x
        factor = p.header['nx'] / data.shape[0]
    elif sz is not None:
        pix_size = sz
    else:
        raise ValueError('No parent or pixel-value provided for new mrc file')

    o_file.voxel_size = pix_size * factor
    o_file.nstart = int(round(offset / factor))

    n_head = o_file.header['nlabl']
    if n_head < 10:
        o_file.header['label'][n_head] = f'Created using OccuPy {__version__}'.ljust(80)
        o_file.header['nlabl'] = n_head + 1
    n_head = o_file.header['nlabl']
    if n_head < 10:
        o_file.header['label'][n_head] = f'{extra_header}'.ljust(80)
        o_file.header['nlabl'] = n_head + 1
    o_file.flush()
    o_file.validate()
    o_file.close()


    if parent is not None:
        p.close()
    if verbose:
        if log is None:
            print(f'Wrote new file {file_name}')
        else:
            print(f'Wrote {file_name}', file=log)

def adjust_to_parent(
        file_name: str,
        parent: str
):

    m = mf.open(file_name,'r+')
    p = mf.open(parent)
    offset_p = p.header['nxstart']
    pix_size_p = p.voxel_size.x

    factor = p.header['nx'] / m.header['nx']

    m.voxel_size = pix_size_p * factor
    m.nstart = int(round(offset_p / factor))

    m.flush()

    m.close()
    p.close()

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


def unity_map(
        data: np.ndarray
):
    param = [np.min(data), np.max(data)]
    data /= param[1] - param[0]
    data -= param[0]
    return data, param


def rescale_map(
        data: np.ndarray,
        param: np.ndarray
):
    data += param[0]
    data *= param[1] - param[0]
    return data


def match_to_range(
        change: np.ndarray,
        reference: np.ndarray
):
    rp = np.array([np.min(reference), np.max(reference)])
    cp = np.array([np.min(change), np.max(change)])

    change -= cp[0]
    change /= cp[1] - cp[0]

    change *= rp[1] - rp[0]
    change += rp[0]

    return change


def clip_to_range(
        change: np.ndarray,
        reference: np.ndarray
):
    rp = np.array([np.min(reference), np.max(reference)])
    change = np.clip(change, rp[0], rp[1])
    return change


def uniscale_map(
        data: np.ndarray,
        norm: bool = False
):
    param = [np.min(data), np.max(data)]
    data /= param[1] - param[0]
    if norm:
        data -= np.min(data)
    return data


def lowpass(
        data: np.ndarray,
        resolution: float = None,
        pixels: int = None,
        voxel_size: float = None,
        square: bool = False,
        resample: bool = False,
        keep_scale: bool = False
):
    # Test square
    n = np.shape(data)
    assert len(np.unique(np.shape(n))) == 1, "Input array to lowpass is not square"
    assert n[0] % 2 == 0, "Input array size is not even"

    # Test dim
    ndim = len(n)
    assert ndim == 2 or ndim == 3, "Input array to lowpass is not 2 or 3 "

    # Test required input
    assert pixels is not None or voxel_size is not None, "Lowpass needs pixel size or number of pixels."
    assert pixels is not None or resolution is not None, "Lowpass needs a cutoff resolution or number of pixels"

    # Refernce values
    n = np.shape(data)[0]
    ref_scale = np.max(data)

    # FFT forward
    f_data = spfft.rfftn(data) #*2*np.pi/n
    f_data = sp.fft.fftshift(f_data, axes=(0, 1))

    out_voxel_size = None

    # If the output size is specified, then we are resampling
    if pixels is not None:
        keep_shells = int(pixels / 2)
        resample = True
    # Otherwise the voxel size must have been specified
    else:
        keep_shells = int(np.floor((n * voxel_size) / resolution))  # Keep this many of the lower frequencies
        out_voxel_size = np.copy(voxel_size)

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
            return data
        t = np.zeros((2 * keep_shells, 2 * keep_shells, keep_shells + 1), dtype=np.complex64)
        edge = int((2 * keep_shells - n) / 2)
        t[edge:edge + n, edge:edge + n, :-edge] = f_data

    if resample:
        mid_out = keep_shells
        t = np.zeros((2 * keep_shells * np.ones(ndim).astype(int)), dtype=np.complex64)
        t = t[..., keep_shells-1:]
    else:
        mid_out = mid_in
        t = np.zeros(np.shape(f_data),dtype=np.complex64)

    keep_shells = int(np.min([keep_shells,n/2]))
    if ndim == 3:
        t[mid_out - keep_shells:mid_out + keep_shells, mid_out - keep_shells:mid_out + keep_shells, :keep_shells + 1] = \
            f_data[mid_in  - keep_shells:mid_in  + keep_shells, mid_in  - keep_shells:mid_in  + keep_shells, :keep_shells + 1]
    elif ndim == 2:
        t[mid_out - keep_shells:mid_out + keep_shells, :keep_shells + 1] = \
        f_data[mid_in - keep_shells:mid_in + keep_shells, :keep_shells + 1]

    if not square:
        mask = create_circular_mask(2*mid_out, radius=keep_shells+1, dim=ndim)[..., mid_out-1:]
        t = np.multiply(t, mask)

    f_data2 = np.fft.ifftshift(t, axes=(0, 1))
    out_data = spfft.irfftn(f_data2) #* keep_shells / mid_in

    #if keep_scale:
    #    out_data /= np.mean(out_data)/np.mean(data)

    return out_data, out_voxel_size


def lowpass_map_square(
        data: np.ndarray,
        cutoff: float,
        voxel_size: float,
        resample: bool = False,
        keep_scale: bool = False
):
    n = np.shape(data)[0]
    ndim = len(np.shape(data))
    ref_scale = np.max(data)
    assert ndim == 3
    f_data = np.fft.rfftn(data)
    f_data = np.fft.fftshift(f_data, axes=(0, 1))
    cutoff /= voxel_size
    cutoff_level = int(np.floor((n / cutoff) / 2))  # Keep this many of the lower frequencies
    mid = int(n / 2)
    if 2 * cutoff_level > n:
        # Pad instead
        if not resample:
            return data
        t = np.zeros((2 * cutoff_level, 2 * cutoff_level, cutoff_level + 1), dtype=np.complex)
        edge = int((2 * cutoff_level - n) / 2)
        t[edge:edge + n, edge:edge + n, :-edge] = f_data
    else:
        if resample:
            t = f_data[mid - cutoff_level:mid + cutoff_level, mid - cutoff_level:mid + cutoff_level, :cutoff_level + 1]
        else:
            t = np.zeros(np.shape(f_data)).astype(np.complex)
            t[mid - cutoff_level:mid + cutoff_level, mid - cutoff_level:mid + cutoff_level, :cutoff_level + 1] = \
                f_data[mid - cutoff_level:mid + cutoff_level, mid - cutoff_level:mid + cutoff_level, :cutoff_level + 1]
    f_data = np.fft.ifftshift(t, axes=(0, 1))
    r_data = np.fft.irfftn(f_data)
    if keep_scale:
        m = np.mean(r_data)
        r_data = (r_data - m) * (ref_scale / np.max(r_data)) + m
    return r_data


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
        mask = create_circular_mask(cutoff_level, ndim)[:, :, mid_resample:]
        t = f_data[mid - cutoff_level:mid + cutoff_level, mid - cutoff_level:mid + cutoff_level, :cutoff_level + 1]
        # print(t.shape,mask.shape)
        t = np.multiply(t, mask)
    else:
        mask = create_circular_mask(n, ndim, radius=cutoff_level)[:, :, mid - 1:]
        # print(f_data.shape,mask.shape,mask.sum(),mask.size,n,cutoff_level)
        t = np.multiply(f_data, mask)

    f_data = np.fft.ifftshift(t, axes=(0, 1))
    r_data = np.fft.irfftn(f_data)
    if keep_scale:
        m = np.mean(r_data)
        r_data = (r_data - m) * (ref_scale / np.max(r_data)) + m
    return r_data
