import numpy as np
import mrcfile as mf


def create_circular_mask(
        s: int,
        dim: int,
        soft: bool = False,
        center: int = None,
        radius: int = None
):
    if center is None:  # use the middle of the image
        center = int(s / 2)

    if radius is None:
        radius = center

    if s % 2 == 0:
        center -= 0.5
        radius -= 0.5

    if dim == 2:
        x, y = np.ogrid[:s, :s]
        dist_from_center = np.sqrt((x - center) ** 2 + (y - center) ** 2)
    elif dim == 3:
        x, y, z = np.ogrid[:s, :s, :s]
        dist_from_center = np.sqrt((x - center) ** 2 + (y - center) ** 2 + (z - center) ** 2)
    else:
        raise ValueError('Mask dimension is not 2 or 3 ')

    if soft:  # TODO fix
        raise ValueError('Ah, poor implementation, do not use soft circular mask right now.')
        dist_from_center = np.divide(dist_from_center <= radius, dist_from_center, where=dist_from_center != 0)

    mask = (dist_from_center <= radius)
    return mask


def new_mrc(
        data: np.ndarray,
        file_name: str,
        parent: str = None,
        verbose: bool = False
):
    pix_size = 1.0
    if parent is not None:
        p = mf.open(parent)
        pix_size = p.voxel_size
        p.close()
    o_file = mf.new(file_name, overwrite=True)
    o_file.set_data(data.astype(np.float32))
    o_file.voxel_size = pix_size
    o_file.flush()
    o_file.close()
    if verbose:
        print(f'Wrote new file {file_name}')


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
    cutoff_level = int(np.floor(2 * (n / cutoff)))  # Keep this many of the lower frequencies
    mid = int(n / 2)
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
        cutoff: float,
        voxel_size: float,
        resample: bool = False,
        keep_scale: bool = False
):
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
