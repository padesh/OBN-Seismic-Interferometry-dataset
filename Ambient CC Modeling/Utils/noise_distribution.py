import os
import sys
import yaml
import numpy as np
import matplotlib.pyplot as plt

# ---------------------- Noise Distribution Functions ----------------------

def uniform_distribution(d, mask_noise):
    print('  - Making a Uniform distribution')
    mask_noise[:] += d['weight']
    return mask_noise

def gaussian_distribution(d, n, mask_noise, xcoor, ycoor):
    print(f'  - Making Gaussian blob #{n}')
    x0 = d['center_x'][n]
    y0 = d['center_y'][n]
    theta = np.deg2rad(d.get('azimuth', [0]*len(d['center_x']))[n])
    cos_theta, sin_theta = np.cos(theta), np.sin(theta)

    # Apply azimuthal rotation
    x_rot = (xcoor - x0) * cos_theta + (ycoor - y0) * sin_theta
    y_rot = -(xcoor - x0) * sin_theta + (ycoor - y0) * cos_theta

    gaussian = np.exp(-((x_rot**2 / (2 * d['sigma_x'][n]**2)) +
                        (y_rot**2 / (2 * d['sigma_y'][n]**2))))
    mask_noise += gaussian * d['weight'][n]
    return mask_noise

def disk(d, mask_noise, xcoor, ycoor):
    print('  - Making a Disk distribution')
    x0, y0 = d['center_x'], d['center_y']
    dist = np.sqrt((xcoor - x0)**2 + (ycoor - y0)**2)
    mask = (dist >= d['r1']) & (dist <= d['r2'])
    mask_noise *= np.where(mask, d['weight'], 0)
    return mask_noise

def blocks(d, n, mask_noise, xcoor, ycoor):
    print(f'  - Making Block #{n}')
    x0, y0 = d['center_x'][n], d['center_y'][n]
    wx, wy = d['width_x'][n] / 2, d['width_y'][n] / 2

    dx, dy = np.diff(np.unique(xcoor))[0], np.diff(np.unique(ycoor))[0]
    x1, x2 = int((x0 - wx) // dx), int((x0 + wx) // dx)
    y1, y2 = int((y0 - wy) // dy), int((y0 + wy) // dy)

    mask = np.zeros_like(mask_noise)
    mask[x1:x2, y1:y2] = d['weight'][n]

    # Smooth the block with 1D convolutions
    for _ in range(10):
        mask = np.apply_along_axis(
            lambda row: np.convolve(row, np.ones(6) / 6, mode='same'), axis=1, arr=mask
        )
    for _ in range(10):
        mask = np.apply_along_axis(
            lambda col: np.convolve(col, np.ones(6) / 6, mode='same'), axis=0, arr=mask
        )

    mask_noise += mask
    return mask_noise

def random(d, mask_noise):
    print('  - Making a Random distribution')
    nx, ny = mask_noise.shape
    mask = np.zeros_like(mask_noise)
    for _ in range(mask_noise.size // 10):
        idx = np.random.randint(0, nx)
        idy = np.random.randint(0, ny)
        mask[idx, idy] = d['weight']
    mask_noise += mask
    return mask_noise

# ---------------------- Utilities ----------------------

def load_station_info(filepath):
    with open(filepath, 'r') as f:
        return np.array([line.strip().split() for line in f], dtype=float)

def parse_mesh_params(filepath):
    xmax = ymax = None
    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith('LATITUDE_MAX'):
                ymax = float(line.split('=')[1])
            elif line.startswith('LONGITUDE_MAX'):
                xmax = float(line.split('=')[1])
                break
    return xmax, ymax

# ---------------------- Main ----------------------

def main(example_dir):
    station_file = os.path.join(example_dir, 'DATA/STATIONS_NOISE')
    data_dir = os.path.join(example_dir, 'DATA')
    noise_par = os.path.join(data_dir, 'parfile_noise.yaml')
    obn_stations_file = os.path.join(data_dir, 'STATIONS_OBN')

    # Load station grid information
    station_info = load_station_info(station_file)
    y_index, x_index = station_info[:, 0].astype(int), station_info[:, 1].astype(int)
    ny, nx = y_index.max() + 1, x_index.max() + 1
    ycoor = station_info[:, 2].reshape(nx, ny)
    xcoor = station_info[:, 3].reshape(nx, ny)
    mask_noise = np.zeros((nx, ny))

    # Load noise distribution parameters
    try:
        with open(noise_par, 'r') as f:
            par = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError('parfile_noise.yaml not found in DATA directory.')

    # Generate noise
    print('  - Noise types to distribute:', par['make_noise'])
    for noise_type in par['make_noise']:
        if noise_type == 'uniform':
            mask_noise = uniform_distribution(par['uniform'], mask_noise)
        elif noise_type == 'disk':
            mask_noise = disk(par['disk'], mask_noise, xcoor, ycoor)
        elif noise_type == 'gaussian':
            for n in range(par['gaussian']['n_blobs']):
                mask_noise = gaussian_distribution(par['gaussian'], n, mask_noise, xcoor, ycoor)
        elif noise_type == 'blocks':
            for n in range(par['blocks']['n_blocks']):
                mask_noise = blocks(par['blocks'], n, mask_noise, xcoor, ycoor)
        elif noise_type == 'random':
            mask_noise = random(par['random'], mask_noise)
        else:
            print(f'  - Warning: Undefined noise distribution "{noise_type}"')

    # Normalize
    mask_noise /= mask_noise.max()

    # Load OBN station coordinates # subsampled by 5
    obn_info = load_station_info(obn_stations_file)
    obn_x, obn_y = obn_info[:, 3], obn_info[:, 2]
    obny_index, obnx_index = obn_info[:, 0].astype(int), obn_info[:, 1].astype(int)
    onbny, obnnx = obny_index.max() + 1, obnx_index.max() + 1
    obn_y = obn_y.reshape(obnnx, onbny)[::5, ::5]
    obn_x = obn_x.reshape(obnnx, onbny)[::5, ::5]



    # Get plotting extent from mesh
    xmax, ymax = parse_mesh_params(os.path.join(data_dir, 'meshfem3D_files/Mesh_Par_file'))

    # Plot
    fig, ax = plt.subplots()
    im = ax.scatter(xcoor[::5,::5] / 1000, ycoor[::5,::5] / 1000, c=mask_noise[::5,::5], cmap='viridis', s=2, marker='o', label='Noise distribution')
    ax.scatter(obn_x / 1000, obn_y / 1000, color='r', marker='^', s=1, label='OBN stations')
    ax.set_xlim([0, xmax / 1000])
    ax.set_ylim([0, ymax / 1000])
    ax.set_aspect('equal')
    ax.set_xlabel('x [km]')
    ax.set_ylabel('y [km]')
    ax.invert_yaxis()
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')

    cbar = plt.colorbar(im, orientation='horizontal', pad=0.1, aspect=50)
    cbar.set_label('Noise Relative Strength')

    plt.title('OBNs and Noise Distribution (subsampled by 5)')

    ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=8, borderaxespad=0.)
    plt.tight_layout()
    plt.savefig(f"{data_dir}/noise_distribution_mask+OBNs.png", dpi=300)

    plt.close()

    # Save output
    np.savetxt(f'{data_dir}/NOISE_DISTRIBUTION', mask_noise, fmt='%.3f')

# ---------------------- Entry Point ----------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Usage: python script.py <example_dir>")
    main(sys.argv[1])
