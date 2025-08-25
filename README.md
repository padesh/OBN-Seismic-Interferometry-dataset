# First-order Control Factors for Ocean-bottom Ambient Seismology Interferometric Observations  

Pandey, A., Girard, A., & Shragge, J. (2025). First-order Control Factors for Ocean-bottom Ambient Seismology Interferometric Observations. EarthArXiv eprints, X5R143.

The dataset associated with this work is publicly available on Zenodo:

[Download Dataset](https://doi.org/10.5281/zenodo.16941774)



---

## Dataset Organization  
- The datasets are organized according to the sections of the paper.  
- Data files are stored as **NumPy arrays (`.npy`)**.  
- Axis information for each dataset is provided in corresponding text files.  

---

## Usage  

### Sections 3.3.1 and 3.3.2
For these sections, the velocity/dispersion tensors are stored in a **single `.npy` file**.  You can load and access them as follows:  

```
import numpy as np

# Load the file
data = np.load("file_name.npy", allow_pickle=True).item()

# Access individual components
Crr = data["Crr"]
Cvv = data["Cvv"]
Crv = data["Crv"]
```

### Other Sections
For these sections, the velocity VSG/dispersion are stored in a **single `.npy` file**. You can load and access them as follows:  

```
import numpy as np

data = np.load("file_name.npy")
``` 
## Ambient CC modeling

A sample example for ambient CC modeling using Specfem3D Cartesian is provided in the folder:

Ambient CC modeling/

For any questions, email at apandey@mines.edu
