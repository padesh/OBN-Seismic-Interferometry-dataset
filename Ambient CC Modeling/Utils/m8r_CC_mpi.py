import os
import sys
import shutil
import numpy as np
from mpi4py import MPI
import m8r

# Initialize MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

def custom_sort(file_name):
    try:
        parts = file_name.split('.')
        return int(parts[0]), int(parts[1])
    except ValueError:
        print(f"Warning: Unexpected filename format: {file_name}")
        return (float('inf'), float('inf'))

def read_data_column(file_path):
    with open(file_path, 'r') as file:
        content = file.readlines()
    data = [float(line.split()[1]) for line in content]
    return np.array(data)

def np_to_rsf(nt, nx, ny, dt, dx, dy, ot, ox, oy, file_name):
    file_name = f"{file_name}.rsf"
    Fo = m8r.Output(file_name)
    Fo.put('n1', nx )
    Fo.put('n2', ny )
    Fo.put('n3', nt)
    Fo.put('d1', dx / 1000)
    Fo.put('d2', dy / 1000)
    Fo.put('d3', dt)
    Fo.put('o1', ox / 1000)
    Fo.put('o2', oy / 1000)
    Fo.put('o3', ot)
    Fo.put('label1', 'X')
    Fo.put('label2', 'Y')
    Fo.put('label3', 't')
    Fo.put('unit1', 'km')
    Fo.put('unit2', 'km')
    Fo.put('unit3', 's')
    return Fo

def make_data_volume(example_dir='', data_type='v', icomp='Z', jcomp='X', fname='data_volume'):
    seismogram_dir = os.path.join(example_dir, 'OUTPUT_FILES_step2')
    station_file = os.path.join(example_dir, 'DATA/STATIONS_OBN')
    rsf_dir = os.path.join(example_dir, 'RSF')
    os.makedirs(rsf_dir, exist_ok=True)

    if not os.path.exists(seismogram_dir):
        raise ValueError(f"Directory {seismogram_dir} does not exist.")

    file_list = [file.name for file in os.scandir(seismogram_dir)
                 if file.is_file() and file.name.endswith(f'{jcomp}.sem{data_type}')]
    sorted_files = sorted(file_list, key=custom_sort)
    last_file = sorted_files[-1]
    parts = last_file.split('.')
    ny = int(parts[1]) + 1
    nx = int(parts[0]) + 1
    #print(f"nx={nx}, ny={ny}")

    with open(f"{seismogram_dir}/{last_file}", 'r') as file:
        content = file.readlines()
    time_axis = np.array([float(line.split()[0]) for line in content])
    dt = time_axis[1] - time_axis[0]
    tf = time_axis[-1]
    nt = len(time_axis)
    ot = -(nt - 1) * dt / 2

    if not os.path.exists(station_file):
        raise ValueError(f"File {station_file} does not exist.")

    with open(station_file, 'r') as file:
        lines = [file.readline() for _ in range(ny + 1)]

    col_3 = [float(line.split()[3]) for line in lines]
    col_2 = [float(line.split()[2]) for line in lines]
    dx = col_3[ny] - col_3[0]
    dy = col_2[1] - col_2[0]
    ox = col_3[0]
    oy = col_2[0]

    data = np.empty((nx, ny // size, nt), dtype=np.float32)

    if np.round(dt, 3) <= .001:
        Code = 'F'
    elif np.round(dt, 3) <= .004:
        Code = 'C'
    elif np.round(dt, 3) > .004:
        Code = 'H'
    else:
        raise ValueError("Invalid station code.")

    for j_local, j in enumerate(range(rank, ny, size)):
        for i in range(nx):
            #print(f"Rank {rank} reading {i}.{j}.{Code}X{jcomp}.sem{data_type}")
            file_name = f"{i}.{j}.{Code}X{jcomp}.sem{data_type}"
            file_path = os.path.join(seismogram_dir, file_name)
            data[i, j_local, :] = read_data_column(file_path)

    if rank == 0:
        received_data = np.empty((size, nx, ny // size, nt), dtype=np.float32)
    else:
        received_data = None

    comm.Gather(data, received_data, root=0)

    if rank == 0:
        final_data = np.empty((nx, ny, nt), dtype=np.float32)
        for i in range(size):
            final_data[:, i::size, :] = received_data[i]
        Fo = np_to_rsf(nt, nx, ny, dt, dx, dy, ot, ox, oy, f"C{icomp}{jcomp}_{fname}")
        Fo.write(np.transpose(final_data, (2, 1, 0)))
        Fo.close()
        shutil.move(f"C{icomp}{jcomp}_{fname}.rsf", os.path.join(rsf_dir, f"C{icomp}{jcomp}_{fname}.rsf"))

if __name__ == "__main__":    
    if len(sys.argv) < 5:
        raise ValueError("Usage: python m8r_CC_mpi.py <example_dir> <data_type> <icomp> <jcomp> <fname>")

    example_dir = str(sys.argv[1])
    data_type = str(sys.argv[2])
    icomp = str(sys.argv[3]) #
    jcomp = str(sys.argv[4])
    if len(sys.argv) == 6:
        fname = str(sys.argv[5])
    else:
        fname = ''

    make_data_volume(example_dir, data_type, icomp, jcomp, fname)