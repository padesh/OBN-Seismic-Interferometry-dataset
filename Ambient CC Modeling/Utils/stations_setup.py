from __future__ import print_function

import os
import sys
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def stations(
    ymin, ymax, dy,
    ystart, yend,
    xmin, xmax, dx,
    xstart, xend,
    z,
    x_y_sampling=1,
    rtype="OBN",
    example_dir=".",
    sx=0, sy=0, sz=0,
):
    """
    Generate 3D and 2D receiver station layout and save to DATA.
    """
    if yend // (dy * x_y_sampling) == 0: #include the last value if it is an integer multiple of dy
        yend = ystart + dy * x_y_sampling 
    if xend // (dx * x_y_sampling) == 0: #include the last value if it is an integer multiple of dx
        xend = xstart + dx * x_y_sampling

    # Create receiver coordinate grid
    ry = np.arange(ystart, yend , dy * x_y_sampling)
    rx = np.arange(xstart, xend , dx * x_y_sampling)

    nrec_y = len(ry)
    nrec_x = len(rx)

    rec = np.empty((nrec_y * nrec_x, 4))
    rec[:, 0] = np.tile(ry, nrec_x)  # Y
    rec[:, 1] = np.repeat(rx, nrec_y)  # X
    rec[:, 2] = 0.0                   # Dummy Z
    rec[:, 3] = z                     # Actual depth

    print(f"   Setting up {rtype} stations at depth {z} m from top surface")

    # Create index labels for DataFrame
    y_index = [str(j) for _ in rx for j in range(nrec_y)]
    x_index = [str(i) for i in range(nrec_x) for _ in ry]

    df = pd.DataFrame(rec, columns=["Y", "X", "Z_dummy", "Z"])
    df.insert(0, "sta_x_index", x_index)
    df.insert(0, "sta_y_index", y_index)

    # Format and write to STATIONS file
    output_str = df.to_string(header=False, col_space=8, index=False)
    output_str = "\n".join(line.lstrip() for line in output_str.split("\n"))

    data_dir = os.path.join(example_dir, "DATA")
    os.makedirs(data_dir, exist_ok=True)

    stations_file = os.path.join(data_dir, f"STATIONS_{rtype}")
    with open(stations_file, "w") as f:
        f.write(output_str)

    # ----------- 3D Scatter Plot -----------
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(
        rec[:, 1] / 1000, rec[:, 0] / 1000, rec[:, 3],
        c=rec[:, 3], cmap="viridis_r", s=0.1, marker="o"
    )

    if rtype == "OBN":
        ax.scatter(sx / 1000, sy / 1000, sz, c="r", marker="x")

    ax.set_xlabel("X (km)")
    ax.set_ylabel("Y (km)")
    ax.set_zlabel("Z (m)")
    ax.view_init(30, 30)
    ax.invert_zaxis()
    ax.tick_params(axis="both", which="major", labelsize=6)
    ax.set_xlim(xmin / 1000, xmax / 1000)
    ax.set_ylim(ymin / 1000, ymax / 1000)

    fig.savefig(os.path.join(data_dir, f"STATIONS_{rtype}.png"), dpi=300)
    plt.close(fig)

    # ----------- 2D Plan View -----------
    fig, ax = plt.subplots()
    sc = ax.scatter(
        rec[:, 1] / 1000, rec[:, 0] / 1000,
        c=rec[:, 3], cmap="viridis_r", s=0.1
    )

    if rtype == "OBN":
        ax.plot(sx / 1000, sy / 1000, "r^", markersize=5)
        print(f"   Virtual shot point at X={sx/1000:.3f} km, Y={sy/1000:.3f} km")

    ax.set_xlim(xmin / 1000, xmax / 1000)
    ax.set_ylim(ymin / 1000, ymax / 1000)
    ax.set_xlabel("X (km)")
    ax.set_ylabel("Y (km)")
    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")
    ax.invert_yaxis()
    ax.set_aspect("equal", adjustable="box")
    plt.colorbar(sc, label="Z (m)")

    fig.savefig(os.path.join(data_dir, f"STATIONS2D_{rtype}.png"), dpi=300)
    plt.close(fig)


def usage():
    print("Usage: stations.py ymin ymax dy ystart yend xmin xmax dx xstart xend z x_y_sampling rtype example_dir [sx sy sz]")


if __name__ == "__main__":
    if len(sys.argv) < 15:
        usage()
        sys.exit(1)

    # Parse required arguments
    ymin = float(sys.argv[1].replace("d", "e"))
    ymax = float(sys.argv[2].replace("d", "e"))
    dy = float(sys.argv[3])
    ystart = float(sys.argv[4])
    yend = float(sys.argv[5])
    xmin = float(sys.argv[6].replace("d", "e"))
    xmax = float(sys.argv[7].replace("d", "e"))
    dx = float(sys.argv[8])
    xstart = float(sys.argv[9])
    xend = float(sys.argv[10])
    z = float(sys.argv[11].replace("d", "e"))
    x_y_sampling = float(sys.argv[12])
    rtype = sys.argv[13]
    example_dir = sys.argv[14]

    # Optional source location
    if rtype == "OBN":
        sx = float(sys.argv[15])
        sy = float(sys.argv[16])
        sz = float(sys.argv[17])
    else:
        sx = sy = sz = 0

    # Call main function
    stations(
        ymin, ymax, dy,
        ystart, yend,
        xmin, xmax, dx,
        xstart, xend,
        z,
        x_y_sampling,
        rtype,
        example_dir,
        sx, sy, sz
    )
