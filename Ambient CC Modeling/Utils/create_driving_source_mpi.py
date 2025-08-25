#!/usr/bin/env python

import os
import sys
import array
import numpy as np
from mpi4py import MPI
from scipy.signal import butter, filtfilt

# --------------------- MPI SETUP --------------------- #
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# --------------------- ARGUMENT PARSING --------------------- #
if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Usage: python create_driving_source_mpi.py example_dir [freq_lp]")

    example_dir = str(sys.argv[1])
    cc_type= str(sys.argv[2])
    if sys.argv[3] != 'None':
        freq_lp = float(sys.argv[3])
    else:
        freq_lp = 'None'

# --------------------- PATH DEFINITIONS --------------------- #
seismogram_dir = os.path.join(example_dir, 'OUTPUT_FILES_step1')
data_dir = os.path.join(example_dir, 'DATA')
sources_dir = os.path.join(data_dir, 'SOURCES')
station_file = os.path.join(data_dir, 'STATIONS_NOISE')

# --------------------- HELPER FUNCTIONS --------------------- #
def write_binary_file(filename, data):
    """
    Write 1D numpy array to a Fortran-style binary file.
    """
    custom_type = 'f'  # 'f' for float32
    num_points = data.size
    binlength = array.array('i', [num_points * 4])
    binvalues = array.array(custom_type, np.reshape(data, (num_points), order='F').tolist())

    with open(filename, mode='wb') as f:
        binlength.tofile(f)
        binvalues.tofile(f)
        binlength.tofile(f)

def lowpass_filter(data, dt, freq_lp, order=4):
    """
    Apply low-pass Butterworth filter.
    """
    fs = 1.0 / dt
    nyquist = 0.5 * fs
    normal_cutoff = freq_lp / nyquist
    b, a = butter(order, normal_cutoff, btype='low')
    return filtfilt(b, a, data)

def process_trace(file, noise_mask):
    """
    Process a single seismogram file: reverse, taper, mask, and write.
    """
    file_path = os.path.join(seismogram_dir, file)
    x, y = map(int, file.split('.')[:2])

    trace = np.loadtxt(file_path, dtype=float, comments='#')
    dt = trace[1, 0] - trace[0, 0] # Time step
    w_ot_shift = -1 * trace[0, 0] # Wavelet origin time shift

    #Time reversal
    reversed_trace = np.flip(trace[:, 1])
    # Padding to make length equal to 2*N-1 steps. N=causal time steps
    pad_len = len(reversed_trace) - 2 * int(w_ot_shift // dt) - 1  
    padded_trace = np.pad(reversed_trace, (0, pad_len), mode='constant') * noise_mask[x, y]

    #Postprocess the trace

    # Apply cosine taper at both ends
    taper = np.ones(len(padded_trace))
    n_taper = int(0.05 * len(padded_trace))
    cosine_window = 0.5 * (1 - np.cos(np.linspace(0, np.pi, n_taper)))
    taper[:n_taper] = cosine_window
    taper[-n_taper:] = cosine_window
    padded_trace *= taper

    # Apply low-pass filter if specified
    if freq_lp!= 'None':
        padded_trace = lowpass_filter(padded_trace, dt, freq_lp)
    
    if cc_type in ['pressure', 'velocity']:
        if cc_type == 'velocity':
            padded_trace = -1 * padded_trace 
    else:
        raise ValueError("Invalid cc_type. Use 'velocity' or 'pressure.")

    # Write the processed trace to a binary file
    output_path = os.path.join(sources_dir, f'{x}.{y}.P.bin')
    write_binary_file(output_path, padded_trace)

def create_cmtsolutions(data_dir, station_file):
    """
    Create CMTSOLUTION file for P-type sources.
    """
    with open(station_file, 'r') as f:
        station_info = [line.strip().split() for line in f]

    with open(os.path.join(data_dir, 'CMTSOLUTION'), 'w') as f:
        for idx, station in enumerate(station_info):
            lat, lon = float(station[2]), float(station[3])
            depth = float(station[5]) / 1000

            f.write(f'PDE 1999 01 01 00 00 00.00  {lat} {lon} {depth} 1 1 test{idx+1:03d}\n')
            f.write(f'event name:      {idx + 1:03d}\n')
            f.write('time shift:       0.0000\n')
            f.write('half duration:    0.0\n')
            f.write(f'latorUTM:       {lat}\n')
            f.write(f'longorUTM:      {lon}\n')
            f.write(f'depth:          {depth}\n')
            f.write('Mrr:        1\n')
            f.write('Mtt:        1\n')
            f.write('Mpp:        1\n')
            f.write('Mrt:        0\n')
            f.write('Mrp:        0\n')
            f.write('Mtp:        0\n')
            f.write(f'DATA/SOURCES/{station[1]}.{station[0]}.P.bin\n')

# --------------------- FILE COLLECTION & DISTRIBUTION --------------------- #

files = [f.name for f in os.scandir(seismogram_dir) if f.name.endswith('P.semp')]

batch = np.array_split(files, size)
noise_mask = np.loadtxt(os.path.join(data_dir, 'NOISE_DISTRIBUTION'), dtype=float)

# --------------------- PROCESSING --------------------- #
for file in batch[rank]:
    process_trace(file, noise_mask)

comm.Barrier()  # Synchronize all MPI processes

# ---------------------Generating CMTSOLUTIONS file in DATA/ for Step-2 run (ONLY RANK 0) ------------- #
if rank == 0:
    create_cmtsolutions(data_dir, station_file)

