#!/bin/bash

#SBATCH --job-name=specfem
#SBATCH --output=SLURM_OUTPUT/%j.out
#SBATCH --error=SLURM_OUTPUT/%j.err
#SBATCH --nodes=3
#SBATCH --ntasks-per-node=25
#SBATCH --time=10:00:00

module load apps/python3
conda activate VSCode 


EXAMPLE_DIR=$(pwd)
UTILS_DIR="$EXAMPLE_DIR/Utils"

fname='Saltmodel'       #file name for RSF shotfather cube
data_type='v'           #data type for Cross-correlation virtual shotgather cube: v for velocity, p for pressure d for displacement
icomp='Z'               #direction of source injected at virtual shot point: Z/Y/X/P for vertical/horizontal/pressure. 
                        #Check sou_rec_setup.sh file for the speficified component

mkdir -p $example_dir/RSF

echo " Creating RSF File!"

run_task () {
    local jcomp=$1
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Task for component $icomp$jcomp initiated."
    srun --nodes=1  --ntasks=25  python $UTILS_DIR/m8r_CC_mpi.py $EXAMPLE_DIR $data_type $icomp $jcomp $fname   
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Task for component $icomp$jcomp completed."
    }

run_task Z &
run_task Y &
run_task X &
wait