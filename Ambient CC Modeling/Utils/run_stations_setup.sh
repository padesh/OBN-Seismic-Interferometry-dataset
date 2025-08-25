#!/bin/bash
#
# Script to set up receiver locations (NOISE or OBN)
#

#------------------------- Usage Check -------------------------#
if [[ "$#" -lt 9 ]]; then
    echo "Usage: ./run_stations_setup.sh example_dir z x_y_sampling type(NOISE/OBN) xstart xend ystart yend utils_dir [sx sy sz]"
    exit 1
fi

#------------------------- Input Parameters --------------------#
example_dir="$1"
z="$2"
x_y_sampling="$3"
rtype="$4"
xstart="$5"
xend="$6"
ystart="$7"
yend="$8"
utils_dir="$9"

# Optional source location inputs for OBN type
if [[ "$rtype" == "OBN" ]]; then
    sx="${10}"
    sy="${11}"
    sz="${12}"
fi

#---------------------- Helper Function ------------------------#
get_mesh_param() {
    local key="$1"
    local file="${2:-DATA/meshfem3D_files/Mesh_Par_file}"
    grep "^${key}" "$file" | grep -v -E '^[[:space:]]*#' | cut -d '=' -f 2 | xargs
}

#---------------------- Read Mesh Parameters -------------------#
ymin=$(get_mesh_param LATITUDE_MIN)
ymax=$(get_mesh_param LATITUDE_MAX)
ny=$(get_mesh_param NEX_ETA)

xmin=$(get_mesh_param LONGITUDE_MIN)
xmax=$(get_mesh_param LONGITUDE_MAX)
nx=$(get_mesh_param NEX_XI)

#---------------------- Calculate Grid Spacing -----------------#
dx=$(echo "scale=2; ($xmax - $xmin) / $nx" | bc)
dy=$(echo "scale=2; ($ymax - $ymin) / $ny" | bc)

#---------------------- Receiver Grid Setup --------------------#
x_y_sampling_float=$(echo "scale=2; $x_y_sampling" | bc)
x_sampling=$(echo "scale=2; $x_y_sampling * $dx" | bc)
y_sampling=$(echo "scale=2; $x_y_sampling * $dy" | bc)


rxmin=$(echo "scale=2; $xstart" | bc)
rxmax=$(echo "scale=2; $xend" | bc)
rymin=$(echo "scale=2; $ystart" | bc)
rymax=$(echo "scale=2; $yend" | bc)

rnx=$(awk "BEGIN {print int(($rxmax - $rxmin) / ($x_sampling) + 1)}")
rny=$(awk "BEGIN {print int(($rymax - $rymin) / ($y_sampling) + 1)}")
x_sampling=$(echo "scale=2; $x_y_sampling * $dx" | bc)
y_sampling=$(echo "scale=2; $x_y_sampling * $dy" | bc)

#---------------------- Output Info ----------------------------#
echo ""
echo "  -Receiver setup parameters:"
echo "   Z depth         : $z m"
echo "   X spacing       : $x_sampling m"
echo "   Y spacing       : $x_sampling m"
echo "   X range         : $rxmin m to $rxmax m, $rnx receivers"
echo "   Y range         : $rymin m to $rymax m, $rny receivers"
echo "   Total receivers : $((rnx * rny))"

#---------------------- Python Execution -----------------------#
python $utils_dir/stations_setup.py \
    $ymin $ymax $dy $ystart $yend \
    $xmin $xmax $dx $xstart $xend \
    $z $x_y_sampling $rtype $example_dir \
    $sx $sy $sz
