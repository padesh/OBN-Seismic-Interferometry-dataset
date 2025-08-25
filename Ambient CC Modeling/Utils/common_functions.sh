#!/bin/bash

#----------------- Functions ----------------------------

safe_rm() { rm -rf "$@" 2>/dev/null; }
safe_cp() { cp "$@" 2>/dev/null; }
safe_mv() { mv "$@" 2>/dev/null; }

msg() {
    # Display a message with a separator line
    echo -e "\n$1\n$(printf '%0.s-' {1..80})"
}

msgb() {
    # Display a centered message with a bounding box of #
    local width=80
    local message="$1"
    local border
    border=$(printf '#%.0s' $(seq 1 $width))
    
    # Strip ANSI codes for length calculation if present
    local clean_message=$(echo -e "$message" | sed 's/\x1b\[[0-9;]*m//g')
    local msg_len=${#clean_message}
    local padding=$(( (width - msg_len) / 2 ))

    # Ensure padding is not negative
    [ $padding -lt 0 ] && padding=0

    local line=$(printf "%*s%s" $padding "" "$message")

    echo -e "\n$border"
    echo "$line"
    echo "$border"
    echo
}



update_par() {
    # Update a Parfile or mesh_Par_file in a file
    local file=$1 key=$2 value="$3"
    sed -i "s|^\s*${key}\s*=.*|${key} = $value|" "$file"
}

get_par_value() {
    # Get the value of a parameter from a file
    local file=$1 key=$2
    grep "^\s*${key}" "$file" | grep -v '^[[:space:]]*#' | cut -d '=' -f2 | tr -d '[:space:]'
}

update_SOLUTIONfile() {
    # Update FORCESOLUTION file
    local file=$1 key=$2 value="$3"
    sed -i "s|^\s*${key}\s*:.*|${key}: $value|" "$file"
}

transfer_files_to_other() {
    mkdir -p OUTPUT_FILES/OTHER_FILES
    cd OUTPUT_FILES || exit
    safe_mv timestamp* movie* start* output* mesh* plot* sr* surface* value* OTHER_FILES
    cd ..
}
