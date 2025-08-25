#!/bin/bash

#==================== Directories and Utilities ====================
EXAMPLE_DIR=$(pwd)
UTILS_DIR="$EXAMPLE_DIR/Utils"

#==================== Load Utility Functions ======================
source "$UTILS_DIR/common_functions.sh" || { echo "Failed to load utilities."; exit 1; }

#==================== User Parameters =============================
# Virtual Source Setup
sx=25500;                    # X coordinate of the virtual source
sy=16500;                   # Y coordinate of the virtual source
sz=850;                     # Z coordinate of the virtual source
stype=FORCE;                # Source type (FORCE)    
icomp=Z;                    # Source component (Z, X, or Y)
f0=0.4                      # Dominant frequency of the Ricker source (Hz) at virtual source location  

#---------------- Receiver Setup ---------------------
z_OBNs=850                  # main reciever depth from surface in m. 
mstartx=12000               # start x location for main recievers
mendx=72000                 # end x location for main recievers 
mstarty=12000               # start y location for main recievers
mendy=72000                 # end y location for main recievers
x_y_sampling_OBNs=0.501     # sampling for recievers in x and y directions relative to grid spacing

#---------------- Ambient Noise Setup --------------------
z_noise=20                  # depth of noise sources from surface in m
nstartx=3000                # start x location for noise sources    
nendx=81000                 # end x location for noise sources
nstarty=3000                # start y location for noise sources
nendy=81000                 # end y location for noise sources
x_y_sampling_noise=1.501    # sampling for recievers at noise locatios in x and y directions relative to grid spacing


#==================== Cleanup Old Files ===========================
echo "  -Cleaning old station, force, and noise files"
safe_rm DATA/STATIONS* DATA/FORCE* DATA/NOISE* DATA/noise* DATA/CMT*

#==================== Setup Noise Receivers =======================
msg "Setting up receivers at noise locations to record \"generating wavefield\" "
$UTILS_DIR/run_stations_setup.sh $EXAMPLE_DIR $z_noise $x_y_sampling_noise NOISE $nstartx $nendx $nstarty $nendy $UTILS_DIR || exit 1
safe_cp $EXAMPLE_DIR/DATA/STATIONS_NOISE $EXAMPLE_DIR/DATA/STATIONS
echo "  -Check DATA/ for receivers at noise locations"

#==================== Setup Main Receivers ========================
msg "Setting up OBN receivers"
$UTILS_DIR/run_stations_setup.sh $EXAMPLE_DIR $z_OBNs $x_y_sampling_OBNs OBN $mstartx $mendx $mstarty $mendy $UTILS_DIR $sx $sy $sz || exit 1
echo "  -Check DATA/ for OBNs"

#==================== Noise Distribution ==========================
msg "Characterizing noise distribution"
echo "  -Check parafile_noise.yaml in DATA/ for noise characterization parameters"
python $UTILS_DIR/noise_distribution.py $EXAMPLE_DIR || exit 1

#==================== Source Setup ================================
msg "Setting up virtual source"
echo "  -Check FORCESOLUTION file in DATA/ for Virtual Source parameters"

depth=$(echo "scale=3; $sz / 1000" | bc)
safe_cp $UTILS_DIR/FORCESOLUTION DATA/

echo "  -Ricker source as ${stype}SOLUTION at X=$sx m, Y=$sy m, Z=$depth km (f0=${f0}Hz)"
update_SOLUTIONfile DATA/FORCESOLUTION "latorUTM" "$sy"
update_SOLUTIONfile DATA/FORCESOLUTION "longorUTM" "$sx"
update_SOLUTIONfile DATA/FORCESOLUTION "depth" "$depth"
update_SOLUTIONfile DATA/FORCESOLUTION "hdurorf0" "$f0"

case "$icomp" in
    Z) update_SOLUTIONfile DATA/FORCESOLUTION "component dir vect source Z_UP" "-1.d0";;
    X) update_SOLUTIONfile DATA/FORCESOLUTION "component dir vect source E" "1.d0";;
    Y) update_SOLUTIONfile DATA/FORCESOLUTION "component dir vect source N" "1.d0";;
    *) msg "Unknown source component: $icomp"; exit 1;;
esac

update_par DATA/Par_file USE_FORCE_POINT_SOURCE .true.
update_par DATA/Par_file USE_RICKER_TIME_FUNCTION .true.
update_par DATA/Par_file USE_EXTERNAL_SOURCE_FILE .false.

#==================== Done ========================================

