----------------------------------------------------------------------
README
----------------------------------------------------------------------

////////////////////////////////WARNING///////////////////////////////////////////
Do ***NOT*** try this example until you have become familiar with the theory in:
First-order Control Factors for Ocean-bottom Ambient Seismology Interferometric Observations (https://eartharxiv.org/repository/view/8821/)
////////////////////////////////WARNING///////////////////////////////////////////


**************
0. README
**************

   This example shows how one can construct low-frequency (sub 1Hz) velocity component noise cross-correlations recorded on OBNs due to ambeint pressure sources acting on ocean-surface. 
   Velocity model used extends to 11km depth with ocean-bottom at 0.8km. 
   Check folder RSF for velcoity files in rsf format for more details. User will need madagascar installed to visulatize these models


**************
1. Structure
**************

   This file                                                                    ---  README
   Folders containing default input files for the example                       ---  ./DATA       
   Utility files may help you to set up ambient sources and recievers           ---  ./Utils
   Job script                                                                   ---  run_this_example.slurm
   Cross-correlation cubes in RSF format                                        ---  makeCCrsf.slurm 


**************
2. Usage
**************

   This example needs fairly large HPC resources. If you have at least 784 CPU cores and mpif90 works on your workstation, you can run this example on your workstation. Simple do (after configuration, for example, "./configure FC=ifort MPIFC=mpif90". Should you be confused, familiarize yourself with other examples first)
   -Install the rquired python modules (listed below) in a virtual invironment. 
   -Edit ./run_this_example.sh to load your virtual environment
   -./run_this_example.slurm

    Make modifications in ./run_this_example.slurm if needed. Change user params in run_this_example.slurm and sou_rec_setup.sh as per your needs. 

    Those commands in ./run_this_example.sh should be self-explanatory.
    You may want to compare them with descriptions in the Manual --- ../../../doc/USER_MANUAL/manual_SPECFEM3D.pdf

**************
3. Results
**************

   At the end of those simulations, outputs will be saved in OUTPUT_FILES_step1 and OUTPUT_FILES_step2 folers. The seismogram in the OUTPUT_FILES_step2 folder are the cross-correlation components with the component specified in icomp specified in the sou_rec_setup.sh file.

   RSF files for cross-coorelation cube are also provided in RSF fodler. 

**************
4. Python modules requirement
**************

   -numpy
   -mpi4py
   -scipy
   -matplotlib
   -pandas
   -pyyaml
   -m8r API from madagascar 


