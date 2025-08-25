#!/bin/bash

#SBATCH --job-name=NoiseCCforward
#SBATCH --output=SLURM_OUTPUT/%j.out
#SBATCH --error=SLURM_OUTPUT/%j.err
#SBATCH --nodes=22
#SBATCH --ntasks=784
#SBATCH --time=10:00:00

start=`date +%s.%N`

###############################################################################
# LOAD MODULES, ACTIVATE ENV and IMPORT FUNCTIONS  
# This script is designed to be run on the CWP cluster
# This script assumes that the user has already compiled the specfem3d code and binaries are in the specified path
# Users should modify the module load, conda activate commands and spefem binary location to match their environment
# Check package requirements in the README file

module load apps/python3
conda activate VSCode


SPECFEM_ORIG_BINARY="/beegfs/sets/cwp/specfem3d/bin_CPU1"
EXAMPLE_DIR=$(pwd)
UTILS_DIR="$EXAMPLE_DIR/Utils"

source "$UTILS_DIR/common_functions.sh" || { echo "Failed to load utilities."; exit 1; }

###############################################################################

#---------------------- USER VARIABLES -----------------------------

NSTEPS=19000        # Number of time steps for the 1st step. The final simulation in step-2 would be 2*(NSTEPS*DT-hdur)-DT as wavelet peak is at t=hdur. hdur is the half duration of the wavelet.
DT=0.004            # Time step in seconds
freq_lp=2           # Low pass filter frequency in Hz for driving force to clean up the records. Set to "None" if not needed.
cc_type=velocity    # Type of CC to be used. Options: velocity, pressure

###############################################################################

# Check if the script is being correctly resource allocated
NPROC_XI=$(get_par_value DATA/meshfem3D_files/Mesh_Par_file NPROC_XI)
NPROC_ETA=$(get_par_value DATA/meshfem3D_files/Mesh_Par_file NPROC_ETA)

if [[ $SLURM_NTASKS -ne $((NPROC_XI * NPROC_ETA)) ]]; then
    echo "Error: SLURM_NTASKS ($SLURM_NTASKS) does not match NPROC_XI * NPROC_ETA ($((NPROC_XI * NPROC_ETA)))"
    exit 1
fi

###############################################################################
# SOURCE RECIVERS SETUP
###############################################################################

msgb "Setting up Sources and Receiver"
echo "  -Edit parameters in sou_rec_setup.sh for your needs"
./sou_rec_setup.sh
[[ $? -ne 0 ]] && echo "Error in running ./run_sou_rec_setup.sh " && exit 1

###############################################################################
# SETUP SIMULATION (STEP 1)
###############################################################################
msgb "Noise Simulation STEP 1"

msg "Running Simulation step 1 Setup"
safe_rm OUTPUT_FILES* DATA/SOURCES
update_par DATA/Par_file LOCAL_PATH ./OUTPUT_FILES/DATABASES_MPI
update_par DATA/Par_file NSTEP "$NSTEPS"
update_par DATA/Par_file DT "$DT"
update_par DATA/Par_file SAVE_SEISMOGRAMS_PRESSURE .true.
update_par DATA/Par_file SAVE_SEISMOGRAMS_DISPLACEMENT .false.
update_par DATA/Par_file SAVE_SEISMOGRAMS_VELOCITY .false.
update_par DATA/Par_file NPROC "$SLURM_NTASKS"
update_par DATA/Par_file GPU_MODE .false.
update_par DATA/Par_file PML_CONDITIONS .true.
update_par DATA/Par_file STACEY_ABSORBING_CONDITIONS .false.


mkdir -p bin OUTPUT_FILES/DATABASES_MPI
cp $SPECFEM_ORIG_BINARY/xmeshfem3D bin/
cp $SPECFEM_ORIG_BINARY/xgenerate_databases bin/
cp $SPECFEM_ORIG_BINARY/xspecfem3D bin/

msg "Running forward simulation"
echo "  -Results dir : $STARTUP_FOLDER/OUTPUT_FILES"
echo "  -Using $SLURM_NTASKS CPUs"

echo "  -Running Mesh Generation"
srun bin/xmeshfem3D || exit 1

echo "  -Running Database Generation"
srun bin/xgenerate_databases || exit 1

echo "  -Running Solver"
srun bin/xspecfem3D || exit 1

transfer_files_to_other
safe_mv OUTPUT_FILES OUTPUT_FILES_step1

###############################################################################
# DRIVING FORCE FOR STEP 2
###############################################################################
msgb "Creating source of the ensemble forward wavefield "
safe_rm DATA/FORCESOLUTION DATA/CMTSOLUTION DATA/SOURCES
mkdir -p DATA/SOURCES

# Using mpi script to create driving force for step 2 due to large number of sources
srun --nodes=1 --ntasks=36 python $UTILS_DIR/create_driving_source_mpi.py $EXAMPLE_DIR $cc_type $freq_lp
[[ $? -ne 0 ]] && echo "Error in creating driving force" && exit 1

###############################################################################
# SETUP FOR STEP 2
###############################################################################
msgb "Noise Simulation STEP 2"

msg "Running Simulation step 2 Setup"
safe_cp DATA/STATIONS_OBN DATA/STATIONS

# Getting nsteps from one of the driving source file
src=$(find DATA/SOURCES -type f -name "*.bin" | head -n1)
if [[ -z "$src" ]]; then echo "No source file found"; exit 1; fi
NSTEP=$(head -c 4 "$src" | od -An -t u4)
NSTEP=$(( NSTEP / 4 ))
echo "  -Time steps for step-2: $NSTEP"

update_par DATA/Par_file NSTEP "$NSTEP"
update_par DATA/Par_file SAVE_MESH_FILES .false.
update_par DATA/Par_file USE_FORCE_POINT_SOURCE .false.
update_par DATA/Par_file USE_EXTERNAL_SOURCE_FILE .true.
update_par DATA/Par_file SAVE_SEISMOGRAMS_VELOCITY .true.
update_par DATA/Par_file SAVE_SEISMOGRAMS_DISPLACEMENT .false.
update_par DATA/Par_file SAVE_SEISMOGRAMS_PRESSURE .false.

mkdir -p OUTPUT_FILES/DATA
safe_cp DATA/Par_file OUTPUT_FILES/DATA
safe_cp DATA/*SOLUTION OUTPUT_FILES/DATA
safe_cp OUTPUT_FILES_step1/OTHER_FILES/surface* OUTPUT_FILES/
safe_cp OUTPUT_FILES_step1/OTHER_FILES/value* OUTPUT_FILES/

safe_rm OUTPUT_FILES/DATABASES_MPI
safe_mv OUTPUT_FILES_step1/DATABASES_MPI OUTPUT_FILES/DATABASES_MPI

###############################################################################
# FORWARD SIMULATION STEP 2
###############################################################################

msg "Running forward simulation"
echo "  -Running Solver"
srun bin/xspecfem3D || exit 1

transfer_files_to_other
safe_mv OUTPUT_FILES OUTPUT_FILES_step2

end=$(date +%s.%N)
runtime=$(echo "$end - $start" | bc -l)
runtime_int=$(printf "%.0f" "$runtime")

mhours=$((runtime_int / 3600))
minutes=$(( (runtime_int % 3600) / 60 ))
seconds=$((runtime_int % 60))

echo " "
echo " Total runtime: $mhours h, $minutes m, $seconds s"

msgb "Simulation completed successfully"